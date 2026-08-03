"""R-271 stop-on-first-failure focused gate for the S17 IMF1 hypothesis."""
from __future__ import annotations

import argparse, bisect, ctypes, hashlib, inspect, json, math, struct, sys, time
from pathlib import Path
import numpy as np
import scipy
from scipy.signal import _peak_finding, _peak_finding_utils
from scipy.signal.windows import _windows

from reference.maf_p0.complex_partial_analyzer import (ComplexPartialAnalyzerManifest,
    observe_complex_partials)
from reference.maf_p0.inharmonic_field_oracle import (Instance, Knot, Mode, decode_model,
    div_even, expand_imu, frozen_basis, pack_imf)
from reference.maf_p0.lapped_oracle import decode_lapped_stream, encode_lapped_stream
from reference.maf_p0.native_core import NativeCoreError, NativeMain0Decoder
from reference.maf_p0.partial_graph_fixed import (LOCALLY_RESOLVABLE, PHASE_USABLE,
    NativePartialGraph, make_manifest, make_observation, make_path_manifest,
    make_resolution)
from reference.maf_p0.wav_io import read_pcm16_channels, write_pcm16_channels
from experiments.r216_s12_metrics import compute_metrics, quality_axes

ROOT = Path(__file__).resolve().parents[1]; MASK32=(1<<32)-1
CONTROL = ROOT / "artifacts/corpus/r271-s17-controls-v1"
PREFLIGHT = ROOT / "docs/reviews/R271_S17_INHARMONIC_MODAL_FIELD_PREFLIGHT_2026-08-03.md"
PREFLIGHT_SHA = "a826da394f9dde734297b577d0b5cdc5fe9bed04864c00ac69ca11c2a67f8add"
REMEDIATION = ROOT / "docs/reviews/R274_S17_IMPLEMENTATION_CLOSURE_REMEDIATION_2026-08-03.md"
REMEDIATION_SHA = "d6059aa85cb16484809a12491f3b40354a26216ba00eed3585f89d739ede2f9b"
SOURCE_CLOSURE = ("native/include/resonith/inharmonic_field.h","native/src/inharmonic_field.cpp","native/tests/inharmonic_field_test.cpp","reference/maf_p0/inharmonic_field_oracle.py","experiments/r271_s17_inharmonic_field_gate.py","experiments/r271_s17_control_freezer.py","native/CMakeLists.txt","reference/maf_p0/complex_partial_analyzer.py","reference/maf_p0/partial_graph_fixed.py","native/include/resonith/partial_graph.h","native/src/partial_graph.cpp","reference/maf_p0/lapped_oracle.py","reference/maf_p0/native_core.py","reference/maf_p0/wav_io.py","experiments/fixtures/r215_cosine_basis_family.json","experiments/fixtures/r271_s17_controls_v1.json","experiments/r216_s12_metrics.py")
PROPOSER_FILES=("reference/maf_p0/complex_partial_analyzer.py","reference/maf_p0/partial_graph_fixed.py","reference/maf_p0/inharmonic_field_oracle.py")
FIXED_SHA={"experiments/r271_s17_control_freezer.py":"06391680f23c9bb771cb7157f2a0e82641e925201d0a081fe696e1f0af30e389","experiments/fixtures/r271_s17_controls_v1.json":"86e772496a2f8c1ecbae89df133ca43528701c716acabffdeb90f27ca9939738","artifacts/corpus/r271-s17-controls-v1/r271_s17_controls_v1.json":"c221431154c8d04c6e3f09f164959baa247c85be47c5653cf30f76d27b0c7180","experiments/fixtures/r215_cosine_basis_family.json":"9880c8f4ad2ac36e5af5302299a8a6dbbe7416b8243f48c786db3a375c40a87c","reference/maf_p0/complex_partial_analyzer.py":"c204aeaf1cc0a37d6808605544447f613ceac1c4e5d20f7dc4d13a68df404a8c","reference/maf_p0/partial_graph_fixed.py":"8a692d9d5894049277ae543b10e29c93ea1466cb4c2b648befd7349683f982bc","native/include/resonith/partial_graph.h":"12733d20b54be6209455800f477bfce9b84951d74699972a646dc492b803d49e","native/src/partial_graph.cpp":"ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05"}
CONTROL_SHA={"p0-exact-language-12s.wav":("ace8cd8c82ab3d3c28216f8ba05b9960ba086dc8c11c90312b0d6f2ce376522c","e6d16edaba6b35f0b5c94892c82e749863f1fd8d38f4db50b14c62663b8beec8"),"n1-independent-drift-180s.wav":("13cfc6b63bc38705c7fa3f67b76ae40615355c73b3191050cf285cfe651ed0c5","098f32a9c2f13b851850038de86b9a8b8272d4935e07eebed6d9aeb50460d354")}

class BoundFailure(RuntimeError):pass
class NativeFailure(RuntimeError):
    def __init__(self,operation:str,status:int):super().__init__(f"{operation} failed: {status}");self.status=status

class Inspection(ctypes.Structure):
    _fields_=[("sample_rate",ctypes.c_uint32),("sample_count",ctypes.c_uint32),("basis_count",ctypes.c_uint32),
        ("mode_count",ctypes.c_uint32),("instance_count",ctypes.c_uint32),("knot_count",ctypes.c_uint32),
        ("truth_bytes",ctypes.c_uint32),("truth_offset",ctypes.c_uint64),("complete_bytes",ctypes.c_uint64),("mode_samples",ctypes.c_uint64)]
class Budget(ctypes.Structure): _fields_=[("remaining",ctypes.c_uint64)]

class Core:
    def __init__(self,path:Path):
        self.lib=ctypes.CDLL(str(path));self.last_render_work=0;p8=ctypes.POINTER(ctypes.c_uint8); p16=ctypes.POINTER(ctypes.c_int16)
        for name in ("resonith_imf_inspect","resonith_imu_inspect"):
            f=getattr(self.lib,name);f.argtypes=[p8,ctypes.c_size_t,ctypes.POINTER(Inspection)];f.restype=ctypes.c_int
        for name in ("resonith_imf_render_model","resonith_imu_render_model"):
            f=getattr(self.lib,name);f.argtypes=[p8,ctypes.c_size_t,p16,ctypes.c_size_t,p16,ctypes.c_size_t,ctypes.POINTER(Budget)];f.restype=ctypes.c_int
        f=self.lib.resonith_imf_fit_decay;f.argtypes=[ctypes.c_uint16,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_uint32),ctypes.c_size_t,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_uint64)];f.restype=ctypes.c_int
    def render(self,payload:bytes,direct=False)->np.ndarray:
        source=(ctypes.c_uint8*len(payload)).from_buffer_copy(payload);info=Inspection(); inspect=getattr(self.lib,"resonith_imu_inspect" if direct else "resonith_imf_inspect")
        status=inspect(source,len(payload),ctypes.byref(info))
        if status==6:raise BoundFailure("native inspect capacity bound")
        if status:raise NativeFailure("native inspect",status)
        basis=np.ascontiguousarray(frozen_basis());out=np.empty(info.sample_count,np.int16);required=info.mode_samples*2+info.sample_count*2;budget=Budget(required);render=getattr(self.lib,"resonith_imu_render_model" if direct else "resonith_imf_render_model")
        status=render(source,len(payload),basis.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),basis.size,out.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),out.size,ctypes.byref(budget))
        if status==6:raise ValueError("native model clipping/profile rejection")
        if status:raise NativeFailure("native model render",status)
        if budget.remaining!=0:raise RuntimeError("native render work accounting mismatch")
        self.last_render_work=required
        return out
    def decay(self,relative:int,offsets:list[int],targets:list[int])->tuple[int,int]:
        a=(ctypes.c_uint32*len(offsets))(*offsets);b=(ctypes.c_uint32*len(targets))(*targets);value=ctypes.c_uint32();work=ctypes.c_uint64()
        status=self.lib.resonith_imf_fit_decay(relative,a,b,len(offsets),ctypes.byref(value),ctypes.byref(work))
        if status==6:raise BoundFailure("native decay capacity bound")
        if status==11:raise ValueError("no admissible decay")
        if status:raise NativeFailure("native decay fit",status)
        return value.value,work.value
    def transactional_witness(self,pack:bytes,direct:bytes)->None:
        p8=ctypes.POINTER(ctypes.c_uint8);p16=ctypes.POINTER(ctypes.c_int16);basis=np.ascontiguousarray(frozen_basis())
        for payload,is_direct in ((pack,False),(direct,True)):
            source=(ctypes.c_uint8*len(payload)).from_buffer_copy(payload);info=Inspection();inspect_fn=getattr(self.lib,"resonith_imu_inspect" if is_direct else "resonith_imf_inspect");render=getattr(self.lib,"resonith_imu_render_model" if is_direct else "resonith_imf_render_model")
            if inspect_fn(source,len(payload),ctypes.byref(info)):raise RuntimeError("transaction witness inspect failed")
            output=(ctypes.c_int16*info.sample_count)(*([1234]*info.sample_count));budget=Budget(1);status=render(source,len(payload),basis.ctypes.data_as(p16),basis.size,output,info.sample_count,ctypes.byref(budget))
            if status!=6 or budget.remaining!=1 or any(x!=1234 for x in output):raise RuntimeError("low-budget transaction witness failed")
        malformed=bytearray(pack);malformed[28]=1;source=(ctypes.c_uint8*len(malformed)).from_buffer_copy(malformed);info=Inspection()
        if self.lib.resonith_imf_inspect(source,len(malformed),ctypes.byref(info))==0:raise RuntimeError("malformed parser witness failed")

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def sha_file(path:Path)->str:return sha(path.read_bytes())
def scipy_identity()->dict:
    modules=(_peak_finding,_peak_finding_utils,_windows)
    return {"version":scipy.__version__,"files":{module.__name__:{"path":str(Path(module.__file__).resolve()),"sha256":sha_file(Path(module.__file__))} for module in modules}}
def validate_fixed_inputs()->dict:
    for relative,expected in FIXED_SHA.items():
        if sha_file(ROOT/relative)!=expected:raise RuntimeError(f"frozen identity changed: {relative}")
    tracked=json.loads((ROOT/"experiments/fixtures/r271_s17_controls_v1.json").read_text(encoding="utf-8"));generated=json.loads((CONTROL/"r271_s17_controls_v1.json").read_text(encoding="utf-8"))
    if tracked!=generated:raise RuntimeError("tracked/generated control manifests differ")
    for name,(wav_sha,pcm_sha) in CONTROL_SHA.items():
        path=CONTROL/name
        if sha_file(path)!=wav_sha:raise RuntimeError(f"control WAV changed: {name}")
        _,frames=read_pcm16_channels(path)
        if sha(frames.astype("<i2",copy=False).tobytes())!=pcm_sha:raise RuntimeError(f"control PCM changed: {name}")
    basis=frozen_basis()
    if sha(basis.astype("<i2",copy=False).tobytes())!="da8b1b6cfbb6840806397707bec13084a272d2746628f0e61acd96cd4c372e7c":raise RuntimeError("Basis PCM identity changed")
    return {"fixed_sha256":FIXED_SHA,"control_sha256":CONTROL_SHA}

def fixed_graph_inputs(observations,rate:int,total_frames:int)->tuple[tuple,tuple,dict]:
    """Reproduce only the frozen observer-to-path conversion needed by S17."""
    rows=tuple(sorted((row for row in observations.observations if row.detector_channel==-1 and row.phase_usable and row.locally_resolvable and 0<=row.center_sample<total_frames),key=lambda row:(row.center_sample,row.resolution_id,row.frequency_hz,row.provenance)))
    resolutions=tuple(make_resolution(index,int(row["fft_samples"]),int(row["hop_samples"])) for index,row in enumerate(observations.report["resolution_manifest"]))
    fixed=[]
    for identifier,row in enumerate(rows):
        amplitude=int(round(row.normalized_detector_amplitude*2.0))
        if not 1<=amplitude<=65536:continue
        frequency=int(round(row.frequency_hz*(1<<20)));uncertainty=max(1,int(round(row.frequency_uncertainty_hz*(1<<20))))
        phase_step=div_even(frequency*(1<<32),rate<<20);phase_uncertainty=min((1<<31)-1,max(1,int(round(row.phase_uncertainty_radians*(1<<31)/math.pi))))
        ownership=row.conflict_group if row.conflict_group>=0 else len(observations.observations)+identifier
        node=max(1,min((1<<31)-1,int(round(math.log2(1.0+row.amplitude_lower_confidence)*256))))
        fixed.append(make_observation(observation_id=len(fixed),frame_index=row.frame_index,resolution_id=row.resolution_id,hop_samples=row.hop_samples,frequency_hz_q20=frequency,phase_turn_u32=int(round(((float(row.aggregate_phase)/(2.0*math.pi))%1.0)*(1<<32)))&MASK32,phase_step_u32=phase_step,normalized_amplitude_q16=amplitude,ownership_component=ownership,detector_id=-1,frequency_uncertainty_hz_q20=uncertainty,phase_uncertainty_u31=phase_uncertainty,flags=PHASE_USABLE|LOCALLY_RESOLVABLE,potential_node_value_q8=node))
    report={"high_level_observations":len(observations.observations),"aggregate_phase_usable_resolvable":len(rows),"fixed_observations":len(fixed)}
    return resolutions,tuple(fixed),report
def qstep(freq_q20:int,rate:int)->int:
    value=div_even(freq_q20*(1<<32),rate*(1<<20))
    if not 0<value<1<<31:raise ValueError("phase step outside (0, Nyquist)")
    return value
def median_even(values:list[int])->int:
    ordered=sorted(int(x) for x in values);middle=len(ordered)//2
    if not ordered:raise ValueError("empty median")
    return ordered[middle] if len(ordered)&1 else div_even(ordered[middle-1]+ordered[middle],2)
def median_mode_zero(values:list[int],mode_zero:int)->int:
    ordered=sorted(int(x) for x in values);middle=len(ordered)//2
    if len(ordered)&1:return ordered[middle]
    lo,hi=ordered[middle-1],ordered[middle]
    return lo if abs(mode_zero-lo)<=abs(hi-mode_zero) else hi
def log2_q20(value_q20:int)->int:
    if value_q20<=0:raise ValueError("non-positive ratio")
    integer=value_q20.bit_length()-21;normalized=value_q20<<max(0,31-(20+integer)) if integer>=0 else value_q20<<(31-20-integer)
    if integer>11:normalized=value_q20>>(integer-11)
    fraction=0
    for bit in range(19,-1,-1):
        normalized=div_even(normalized*normalized,1<<31)
        if normalized>=1<<32:normalized=div_even(normalized,2);fraction|=1<<bit
    return integer*(1<<20)+fraction
def interp(rows:list,t:int,field:str)->int:
    centers=[int(x.center_sample) for x in rows];j=bisect.bisect_left(centers,t)
    if j<len(rows) and centers[j]==t:return int(getattr(rows[j],field))
    if j==0 or j==len(rows):raise ValueError("missing interpolation bracket")
    a,b=rows[j-1],rows[j];return int(getattr(a,field))+div_even((int(getattr(b,field))-int(getattr(a,field)))*(t-int(a.center_sample)),int(b.center_sample)-int(a.center_sample))

def unwrap(rows:list,rate:int)->list[int]:
    out=[int(rows[0].phase_turn_u32)]
    for a,b in zip(rows,rows[1:]):
        expected=out[-1]+qstep(int(a.frequency_hz_q20),rate)*(int(b.center_sample)-int(a.center_sample));delta=(int(b.phase_turn_u32)-expected)&MASK32
        if delta==1<<31:raise ValueError("half-turn phase tie")
        if delta>1<<31:delta-=1<<32
        value=expected+delta
        if not -(1<<63)<=value<1<<63:raise ValueError("unwrapped phase overflow")
        out.append(value)
    return out

def phase_interp(rows:list,unwrapped:list[int],t:int)->int:
    centers=[int(x.center_sample) for x in rows];j=bisect.bisect_left(centers,t)
    if j<len(rows) and centers[j]==t:return unwrapped[j]
    if j==0 or j==len(rows):raise ValueError("missing phase bracket")
    value=unwrapped[j-1]+div_even((unwrapped[j]-unwrapped[j-1])*(t-centers[j-1]),centers[j]-centers[j-1])
    if not -(1<<63)<=value<1<<63:raise ValueError("interpolated phase overflow")
    return value

def phase_uncertainty_at(rows:list,t:int)->int:
    centers=[int(x.center_sample) for x in rows];j=bisect.bisect_left(centers,t)
    if j<len(rows) and centers[j]==t:return int(rows[j].phase_uncertainty_u31)
    if j==0 or j==len(rows):raise ValueError("missing phase-uncertainty bracket")
    return max(int(rows[j-1].phase_uncertainty_u31),int(rows[j].phase_uncertainty_u31))

def thin_knots(tagged_times:list[tuple[int,int]],tracks:list[list],rate:int)->tuple[list[int],int]:
    times=[x[0] for x in tagged_times];owners=[x[1] for x in tagged_times]
    if len(times)<=256:return times,0
    prev=list(range(-1,len(times)-1));nxt=list(range(1,len(times)+1));nxt[-1]=-1;alive=[True]*len(times);error=0
    def removal(i):
        if prev[i]<0 or nxt[i]<0:return 1<<62
        a,b=times[prev[i]],times[nxt[i]];return max(abs(qstep(interp(r,times[i],"frequency_hz_q20"),rate)-div_even(qstep(interp(r,a,"frequency_hz_q20"),rate)*(b-times[i])+qstep(interp(r,b,"frequency_hz_q20"),rate)*(times[i]-a),b-a)) for r in tracks)
    import heapq
    heap=[(removal(i),times[i],owners[i],i) for i in range(1,len(times)-1)];heapq.heapify(heap);remaining=len(times)
    while remaining>256:
        e,_,_,i=heapq.heappop(heap)
        if not alive[i] or e!=removal(i):continue
        error=max(error,e);alive[i]=False;remaining-=1;nxt[prev[i]]=nxt[i];prev[nxt[i]]=prev[i]
        for j in (prev[i],nxt[i]):
            if prev[j]>=0 and nxt[j]>=0:heapq.heappush(heap,(removal(j),times[j],owners[j],j))
    return [t for t,a in zip(times,alive) if a],error

def field_from_tracks(items:list[tuple[int,list]],rate:int,sample_count:int,core:Core)->tuple[bytes,dict]:
    items=sorted(items,key=lambda x:(median_even([int(v.frequency_hz_q20) for v in x[1]]),x[0]));path_ids=tuple(x[0] for x in items);tracks=[x[1] for x in items];start=max(int(r[0].center_sample) for r in tracks);end=min(int(r[-1].center_sample) for r in tracks)
    if end-start<2*rate:raise ValueError("shared support is too short")
    owners={start:min(path_ids),end:min(path_ids)}
    for path_id,rows in items:
        for row in rows:
            center=int(row.center_sample)
            if start<=center<=end:owners[center]=min(path_id,owners.get(center,path_id))
    times,thin_error=thin_knots(sorted(owners.items()),tracks,rate)
    values=[[interp(r,t,"frequency_hz_q20") for t in times] for r in tracks];amps=[[interp(r,t,"normalized_amplitude_q16") for t in times] for r in tracks]
    if any(not 0<=a<=65536 for row in amps for a in row):raise ValueError("amplitude outside Q16 full scale")
    ratios=[1<<20]+[median_even([div_even(values[k][i]*(1<<20),values[0][i]) for i in range(len(times))]) for k in range(1,len(tracks))]
    if any(a>=b for a,b in zip(ratios,ratios[1:])):raise ValueError("non-increasing ratios")
    common=[]
    for i in range(len(times)):
        normalized=[div_even(qstep(values[k][i],rate)*(1<<20),ratios[k]) for k in range(len(tracks))]
        common.append(median_mode_zero(normalized,normalized[0]))
    peaks=[max(amps[k][i] for k in range(len(tracks))) for i in range(len(times))]
    if any(not 1<=peak<=65536 for peak in peaks):raise ValueError("zero or oversized peak")
    gains=[div_even(p*32768,65536) for p in peaks];unwrapped=[unwrap(r,rate) for r in tracks];modes=[];decay_work=0
    for k,r in enumerate(tracks):
        targets=[div_even(amps[k][i]*(1<<31),peaks[i]) for i in range(len(times))];relative=div_even(targets[0]*32768,1<<31)
        if relative==0:raise ValueError("zero relative gain")
        decay,work=core.decay(relative,[t-start for t in times],targets);decay_work+=work
        modes.append(Mode(ratios[k],phase_interp(r,unwrapped[k],start)&MASK32,relative,decay))
    knots=tuple(Knot(t-start,common[i],gains[i]) for i,t in enumerate(times));instances=(Instance(start,end-start,0,knots),);mode_tuple=tuple(modes)
    pack=pack_imf(rate,sample_count,mode_tuple,instances);repeat=pack_imf(rate,sample_count,mode_tuple,instances)
    if sha(pack)!=sha(repeat):raise RuntimeError("IMF repeat packing failed")
    fit=sum(abs(qstep(values[k][i],rate)-div_even(common[i]*ratios[k],1<<20)) for k in range(len(tracks)) for i in range(len(times)))
    phase_uncertainty=tuple(phase_uncertainty_at(rows,start) for rows in tracks)
    return pack,{"start":start,"end":end,"modes":len(modes),"knots":len(knots),"thin_error_q32":thin_error,"decay_work":decay_work,"quantized_fit_error":fit,"path_ids":path_ids,"support":end-start,"instances":1,"_mode_rows":mode_tuple,"_phase_uncertainty":phase_uncertainty,"_instance":instances[0]}

def overlap_and_error(seed:tuple[int,list],neighbor:tuple[int,list])->tuple[int,int,int]:
    seed_id,a=seed;neighbor_id,b=neighbor;start=max(int(a[0].center_sample),int(b[0].center_sample));end=min(int(a[-1].center_sample),int(b[-1].center_sample));overlap=end-start
    if overlap<=0:return overlap,1<<62,neighbor_id
    times=sorted({start,end}|{int(x.center_sample) for rows in (a,b) for x in rows if start<=int(x.center_sample)<=end})
    errors=[abs(log2_q20(div_even(interp(b,t,"frequency_hz_q20")*(1<<20),interp(a,t,"frequency_hz_q20")))) for t in times]
    return overlap,median_even(errors),neighbor_id

def cluster_instances(candidates:list[tuple[bytes,dict]],rate:int,sample_count:int,core:Core)->tuple[list[tuple[bytes,dict]],dict,dict[str,np.ndarray]]:
    """Canonical first-fit clustering into no more than eight shared Bases."""
    cache={};clusters=[];trial_renders=0;render_work=0;phase_rejections=0
    def rendered(pack:bytes)->np.ndarray:
        nonlocal trial_renders,render_work
        key=sha(pack)
        if key not in cache:cache[key]=core.render(pack);trial_renders+=1;render_work+=core.last_render_work
        return cache[key]
    for candidate_pack,candidate in candidates:
        try:candidate_pcm=rendered(candidate_pack).astype(np.int32)
        except BoundFailure:raise
        except (ValueError,NativeFailure):continue
        joined=False
        for cluster in clusters:
            modes=cluster["modes"]
            if len(cluster["instances"])>=16 or cluster["used"].intersection(candidate["path_ids"]) or len(candidate["_mode_rows"])!=len(modes):continue
            if any(abs(a.ratio_q20-b.ratio_q20)>2 for a,b in zip(modes,candidate["_mode_rows"])):continue
            shift=(candidate["_mode_rows"][0].phase_q32-modes[0].phase_q32)&MASK32
            phase_ok=True
            for basis_mode,observed_mode,uncertainty in zip(modes,candidate["_mode_rows"],candidate["_phase_uncertainty"]):
                folded=(basis_mode.phase_q32+div_even(shift*basis_mode.ratio_q20,1<<20))&MASK32;delta=(observed_mode.phase_q32-folded)&MASK32
                if delta==1<<31 or abs(delta if delta<1<<31 else delta-(1<<32))>uncertainty:phase_ok=False;break
            if not phase_ok:phase_rejections+=1;continue
            source=candidate["_instance"];trial=sorted([*cluster["instances"],Instance(source.start,source.duration,shift,source.knots)],key=lambda x:(x.start,x.time_shift_q32))
            try:
                pack=pack_imf(rate,sample_count,modes,tuple(trial));trial_pcm=rendered(pack);expected=cluster["target"]+candidate_pcm
            except BoundFailure:raise
            except (ValueError,NativeFailure,struct.error):continue
            if np.any((expected<-32768)|(expected>32767)) or not np.array_equal(trial_pcm.astype(np.int32),expected):continue
            cluster["instances"]=trial;cluster["target"]=expected;cluster["used"].update(candidate["path_ids"]);cluster["members"].append(candidate);cluster["pack"]=pack;joined=True;break
        if not joined and len(clusters)<8:
            clusters.append({"modes":candidate["_mode_rows"],"instances":[candidate["_instance"]],"target":candidate_pcm,"used":set(candidate["path_ids"]),"members":[candidate],"pack":candidate_pack})
    clustered=[]
    for cluster in clusters:
        instances=cluster["instances"];members=cluster["members"]
        if len(instances)<2:continue
        modes=cluster["modes"];pack=cluster["pack"];repeat=pack_imf(rate,sample_count,modes,tuple(instances))
        if sha(pack)!=sha(repeat):raise RuntimeError("clustered IMF repeat packing failed")
        report={"start":min(x.start for x in instances),"end":max(x.start+x.duration for x in instances),"modes":len(modes),"knots":sum(len(x.knots) for x in instances),"thin_error_q32":max(x["thin_error_q32"] for x in members),"decay_work":sum(x["decay_work"] for x in members),"quantized_fit_error":sum(x["quantized_fit_error"] for x in members),"path_ids":tuple(sorted(cluster["used"])),"support":sum(x.duration for x in instances),"instances":len(instances),"_mode_rows":modes,"_phase_uncertainty":members[0]["_phase_uncertainty"],"_instance":instances[0],"_instances":tuple(instances),"proxy_sse":0}
        clustered.append((pack,report))
    unique={sha(pack):(pack,report) for pack,report in clustered}
    return [unique[key] for key in sorted(unique)],{"trial_renders":trial_renders,"render_work_units":render_work,"basis_cluster_count":len(clusters),"emitted_shared_cluster_count":len(unique),"phase_rejections":phase_rejections},cache

def propose(source:np.ndarray,rate:int,native_core:Path,core:Core)->tuple[list[tuple[bytes,dict]],dict]:
    if source.ndim!=1:return [],{"reason":"unsupported_channels"}
    analyzer=ComplexPartialAnalyzerManifest()
    try:observed=observe_complex_partials(source[:,None],rate,manifest=analyzer)
    except MemoryError as error:raise BoundFailure("observer host-memory bound") from error
    except ValueError as error:
        if "bound" in str(error):raise BoundFailure("observer declared bound") from error
        raise
    resolutions,fixed,fixed_report=fixed_graph_inputs(observed,rate,source.size)
    evidence={"observer_report_sha256":sha(json.dumps(observed.report,sort_keys=True,default=str).encode()),"fixed_report":fixed_report,"fixed_observation_count":len(fixed)}
    if not fixed:return [],evidence
    graph=NativePartialGraph(native_core);manifest=make_manifest(sample_rate=rate,resolution_count=len(resolutions),cycle_offsets=(0,),maximum_edge_records=1_000_000)
    try:edges=graph.edges(resolutions,fixed,manifest)
    except RuntimeError as error:
        if str(error).endswith(": 6"):raise BoundFailure("native edge capacity bound") from error
        raise
    family_cap=max(1,min(128,256//3));path_manifest=make_path_manifest(protected_band_upper_hz_q20=tuple(x<<20 for x in (250,1000,4000,12000) if 0<x<rate//2),maximum_path_records=256,
        top_k_value=family_cap,top_k_continuity=family_cap,top_k_protected=family_cap,maximum_total_entries=500_000,maximum_work_units=250_000_000)
    try:result=graph.paths(resolutions,fixed,edges,manifest,path_manifest)
    except RuntimeError as error:
        if str(error).endswith(": 6"):raise BoundFailure("native path capacity bound") from error
        raise
    selected=set(result.selected_path_ids);by_id={int(x.observation_id):x for x in fixed};evidence.update({"edge_count":len(edges),"path_report":result.report,"selected_path_ids":list(sorted(selected))})
    tracks=[]
    for path in result.paths:
        if path.path_id in selected:
            rows=sorted((by_id[int(e.observation_id)] for e in path.entries),key=lambda x:int(x.center_sample))
            if len(rows)>=3:tracks.append((int(path.path_id),rows))
    tracks=sorted(tracks,key=lambda x:x[0])[:64];seeds=sorted(tracks,key=lambda x:(-(int(x[1][-1].center_sample)-int(x[1][0].center_sample)),x[0]));groups=[];seen=set()
    for seed in seeds:
        a,b=int(seed[1][0].center_sample),int(seed[1][-1].center_sample);neighbors=[]
        for candidate in tracks:
            if candidate[0]==seed[0]:continue
            c,d=int(candidate[1][0].center_sample),int(candidate[1][-1].center_sample);overlap=min(b,d)-max(a,c)
            if overlap*2>=min(b-a,d-c):neighbors.append(candidate)
        seed_frequency=median_even([int(x.frequency_hz_q20) for x in seed[1]])
        neighbors=sorted(neighbors,key=lambda x:(abs(median_even([int(v.frequency_hz_q20) for v in x[1]])-seed_frequency),x[0]))[:15]
        neighbors=sorted(neighbors,key=lambda x:(-overlap_and_error(seed,x)[0],overlap_and_error(seed,x)[1],x[0]))
        ordered=[seed,*neighbors]
        for n in range(3,len(ordered)+1):
            key=tuple(x[0] for x in ordered[:n])
            if key not in seen:seen.add(key);groups.append(ordered[:n])
    candidates=[];rejected=0
    for group in groups:
        try:pack,report=field_from_tracks(group,rate,source.size,core)
        except BoundFailure:raise
        except (ValueError,NativeFailure,struct.error):rejected+=1;continue
        candidates.append((pack,report))
    candidates.sort(key=lambda x:(x[1]["quantized_fit_error"],-x[1]["support"],-x[1]["modes"],x[1]["path_ids"]));candidates=candidates[:128];clusters,cluster_evidence,cache=cluster_instances(candidates,rate,source.size,core);evaluated=[];pool={}
    for pack,report in [*candidates,*clusters]:
        key=sha(pack)
        if key in pool and pool[key][0]!=pack:raise RuntimeError("candidate SHA-256 collision")
        pool[key]=(pack,report)
    for key in sorted(pool):
        pack,report=pool[key];model=cache.get(key)
        if model is None:
            try:model=core.render(pack)
            except BoundFailure:raise
            except (ValueError,NativeFailure):rejected+=1;continue
        report["proxy_sse"]=int(np.sum((source.astype(np.int64)-model.astype(np.int64))**2));report["decode_operations"]=2*struct.unpack_from("<Q",pack,80)[0]+2*source.size;report["preroll_samples"]=max(x.duration for x in report.get("_instances",(report["_instance"],)));evaluated.append((pack,report))
    evaluated.sort(key=lambda x:(x[1]["proxy_sse"],len(x[0]),x[1]["modes"],sha(x[0])));evaluated=evaluated[:16];evidence.update({"seed_count":len(seeds),"group_count":len(groups),"rejected_group_count":rejected,"retained_128":[{"path_ids":list(r["path_ids"]),"fit":r["quantized_fit_error"],"support":r["support"],"modes":r["modes"],"pack_sha256":sha(p)} for p,r in candidates],"cluster_evidence":cluster_evidence,"deduplicated_proxy_pool_count":len(pool),"evaluated_order":[sha(p) for p,_ in evaluated]});return evaluated,evidence

def native_scalar_pair(core:Core,pack:bytes)->tuple[np.ndarray,bytes]:
    direct=expand_imu(pack);direct_repeat=expand_imu(pack)
    if sha(direct)!=sha(direct_repeat):raise RuntimeError("IMU repeat packing failed")
    native=core.render(pack);native_direct=core.render(direct,True);_,scalar=decode_model(pack);_,scalar_direct=decode_model(direct)
    if not(np.array_equal(native,native_direct) and np.array_equal(native,scalar) and np.array_equal(native,scalar_direct)):raise RuntimeError("four-way model identity failed")
    return native,direct

def attach_truth(model_pack:bytes,truth:bytes)->bytes:
    pack=bytearray(model_pack);struct.pack_into("<I",pack,24,len(truth));struct.pack_into("<Q",pack,72,len(pack)+len(truth));pack.extend(truth);return bytes(pack)

def truth_slice(payload:bytes)->bytes:
    if payload[:4]==b"IMF1":count=struct.unpack_from("<I",payload,24)[0];offset=struct.unpack_from("<Q",payload,64)[0]
    elif payload[:4]==b"IMU1":count=struct.unpack_from("<I",payload,24)[0];offset=struct.unpack_from("<Q",payload,48)[0]
    else:raise ValueError("unknown pack")
    return payload[offset:offset+count]

def validate_seal(native_core:Path,closure_path:Path,closure_sha:str,receipt_sha:str)->dict:
    if sha_file(PREFLIGHT)!=PREFLIGHT_SHA:raise RuntimeError("preflight identity changed")
    if sha_file(REMEDIATION)!=REMEDIATION_SHA:raise RuntimeError("remediation identity changed")
    if sha_file(closure_path)!=closure_sha:raise RuntimeError("source closure hash mismatch")
    fixed=validate_fixed_inputs();closure=json.loads(closure_path.read_text(encoding="utf-8"));sources=closure.get("sources",{})
    if closure.get("schema")!="resonith-r271-s17-source-closure-1" or closure.get("preflight_sha256")!=PREFLIGHT_SHA or closure.get("remediation_sha256")!=REMEDIATION_SHA or closure.get("baseline_commit")!="e4e2b50c6f43fb26ebf8f9a2f8fa1b174ae61f66" or not 0<closure.get("inclusive_nonblank_lines",0)<=1500 or set(sources)!=set(SOURCE_CLOSURE) or tuple(closure.get("proposer_dependencies",()))!=PROPOSER_FILES:raise RuntimeError("invalid source closure")
    for relative in SOURCE_CLOSURE:
        if sha_file(ROOT/relative)!=sources[relative]:raise RuntimeError(f"source changed after closure: {relative}")
    if sha_file(native_core)!=closure.get("native_core_sha256") or sha_file(Path(sys.executable))!=closure.get("python_executable_sha256") or sys.version!=closure.get("python_version") or np.__version__!=closure.get("numpy_version") or scipy_identity()!=closure.get("scipy_identity"):raise RuntimeError("runtime identity changed after closure")
    compiler=Path(closure.get("compiler_path",""))
    if not closure.get("compiler_identity") or not compiler.is_file() or sha_file(compiler)!=closure.get("compiler_sha256"):raise RuntimeError("compiler identity mismatch")
    forbidden=("r271_s17_control_freezer","r271_s17_controls_v1","auditor_holdout","private_generation_receipt","seed_u64")
    proposer_source="\n".join(inspect.getsource(x) for x in (propose,fixed_graph_inputs,field_from_tracks,cluster_instances,overlap_and_error,thin_knots,unwrap,phase_interp,phase_uncertainty_at,interp,qstep,median_even,median_mode_zero,log2_q20,Core.render,Core.decay))
    dependency_source="\n".join((ROOT/path).read_text(encoding="utf-8") for path in PROPOSER_FILES)
    if any(token in proposer_source or token in dependency_source for token in forbidden):raise RuntimeError("proposer reads a forbidden holdout dependency")
    receipt_path=CONTROL/"p1-auditor-holdout-180s.json";wav=CONTROL/"p1-auditor-holdout-180s.wav"
    if sha_file(receipt_path)!=receipt_sha:raise RuntimeError("auditor receipt hash mismatch")
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"));manifest=json.loads((ROOT/"experiments/fixtures/r271_s17_controls_v1.json").read_text(encoding="utf-8"))
    if receipt.get("schema")!="resonith-r271-s17-auditor-holdout-1" or not 0<=receipt.get("seed_u64",-1)<1<<64 or receipt.get("generator_sha256")!=manifest["generator_sha256"] or receipt.get("wav_sha256")!=sha_file(wav) or receipt.get("wav_bytes")!=wav.stat().st_size:raise RuntimeError("invalid holdout receipt")
    rate,frames=read_pcm16_channels(wav);pcm=frames.astype("<i2",copy=False).tobytes()
    if rate!=receipt.get("sample_rate") or frames.shape!=(receipt.get("sample_count"),1) or sha(pcm)!=receipt.get("pcm16_payload_sha256"):raise RuntimeError("holdout PCM identity mismatch")
    for row in receipt.get("private_generation_receipt",{}).get("instances",[]):
        if row["start_sample"]<0 or row["duration_samples"]<=0 or row["start_sample"]+row["duration_samples"]>frames.shape[0]:raise RuntimeError("truncated holdout instance")
    return {"closure_sha256":closure_sha,"receipt_sha256":receipt_sha,"seed_u64":receipt.get("seed_u64"),"wav_sha256":receipt["wav_sha256"],"pcm_sha256":receipt["pcm16_payload_sha256"],"fixed":fixed,"scipy_identity":scipy_identity()}

def p0(core:Core,validate=True)->dict:
    if validate:validate_fixed_inputs()
    rate,source=read_pcm16_channels(CONTROL/"p0-exact-language-12s.wav");source=source[:,0];ratios=(1048576,1482910,1816164,2344686,2774518,3294198,3780501,4323715);phases=[0x10203040+i*0x13579BDF for i in range(8)];gains=(4200,3100,2500,1900,1450,1100,820,610)
    step=div_even(173*(1<<32),rate);modes=tuple(Mode(r,p,g,1<<31) for r,p,g in zip(ratios,phases,gains));instances=(Instance(0,source.size,0,(Knot(0,step,32768),Knot(source.size,step,32768))),);pack=pack_imf(rate,source.size,modes,instances)
    if sha(pack)!=sha(pack_imf(rate,source.size,modes,instances)):raise RuntimeError("P0 IMF repeat packing failed")
    model,direct=native_scalar_pair(core,pack)
    if not np.array_equal(model,source):raise RuntimeError("P0 exact PCM failed")
    core.transactional_witness(pack,direct)
    if (div_even(4,3),div_even(5,3),div_even(-4,3))!=(1,2,-1):raise RuntimeError("round-even odd-divisor witness failed")
    adversarial_modes=tuple(Mode(r,0,32768,1<<31) for r in ratios[:3]);adversarial_knots=(Knot(0,0,1),Knot(3,4,2),Knot(7,10,2))
    adversarial=pack_imf(rate,7,adversarial_modes,(Instance(0,7,0,adversarial_knots),));native_scalar_pair(core,adversarial)
    return {"status":"PASS","imf_bytes":len(pack),"imu_bytes":len(direct),"pcm_sha256":sha(source.astype("<i2").tobytes()),"odd_divisor_and_interval_witness":"PASS","parser_and_transaction_witness":"PASS"}

def tolerance(path:str)->float:
    if "stoi" in path:return .001
    if "snr_db" in path:return .05
    if "log_mel" in path or "multiresolution_stft" in path:return .01
    if "magnitude_cosine" in path:return .0001
    if "maximum_absolute" in path:return 1.0
    if "rms_error" in path:return .5
    if "log_spectral" in path:return .05
    if "pre_echo" in path:return .1
    if path.endswith(("mae_radians","rmse_radians")):return .001
    return 1e-9

def eligible(candidate:dict,baseline:dict)->bool:
    ca,ba=quality_axes(candidate),quality_axes(baseline)
    if set(ca)!=set(ba):return False
    return all((bv-cv if d=="max" else cv-bv)<=tolerance(k) for k,(d,cv) in ca.items() for _,bv in (ba[k],))

def evaluate_input(core:Core,native_core:Path,path:Path,input_id:str,out:Path,require_model:bool)->dict:
    rate,frames=read_pcm16_channels(path);source=frames[:,0];decoder=NativeMain0Decoder(native_core);case=out/input_id;case.mkdir(parents=True,exist_ok=True);started=time.perf_counter()
    baseline=encode_lapped_stream(frames,rate,coefficients_per_frame=68,half_window=512,band_count=24,entropy_backend="bounded",transform_backend="fixed",density_backend="adaptive",native_analyzer=decoder,native_decoder=decoder)
    baseline_metrics=compute_metrics(frames,baseline.reconstruction,rate,("music",));(case/"baseline.s12.resonith").write_bytes(baseline.payload);write_pcm16_channels(case/"baseline-decoded.wav",rate,baseline.reconstruction);rows=[];rejections=[]
    def capacity_fallback(error:Exception,proposer_evidence:dict|None=None)->dict:
        selected={"representation":"accepted-s12-fallback","complete_bytes":len(baseline.payload),"payload_sha256":sha(baseline.payload)}
        return {"status":"FAIL" if require_model else "PASS","input_id":input_id,"selection":"fallback","bound_hit":str(error),"baseline_bytes":len(baseline.payload),"baseline_sha256":sha(baseline.payload),"baseline_metrics":baseline_metrics,"proposer_evidence":proposer_evidence,"candidates":rows,"rejections":rejections,"selected":selected,"wall_seconds":time.perf_counter()-started}
    try:proposals,proposer_evidence=propose(source,rate,native_core,core)
    except (BoundFailure,MemoryError) as error:
        return capacity_fallback(error)
    try:
        for model_pack,proposal in proposals:
            model,_=native_scalar_pair(core,model_pack);full_model=model;difference=source.astype(np.int32)-full_model.astype(np.int32)
            residual_clip=int(np.count_nonzero((difference<-32768)|(difference>32767)))
            if residual_clip:rejections.append({"reason":"residual_clip","count":residual_clip});continue
            truth_started=time.perf_counter();truth=encode_lapped_stream(difference.astype(np.int16)[:,None],rate,coefficients_per_frame=68,half_window=512,band_count=24,entropy_backend="bounded",transform_backend="fixed",density_backend="adaptive",native_analyzer=decoder,native_decoder=decoder);truth_seconds=time.perf_counter()-truth_started
            pack=attach_truth(model_pack,truth.payload);repeat=attach_truth(model_pack,truth.payload)
            if sha(pack)!=sha(repeat):raise RuntimeError("complete IMF repeat packing failed")
            packed_model,direct=native_scalar_pair(core,pack)
            if not np.array_equal(packed_model,model) or truth_slice(pack)!=truth.payload or truth_slice(direct)!=truth.payload:raise RuntimeError("complete pack Truth/model identity failed")
            residuals=[]
            for complete in (pack,direct):
                payload=truth_slice(complete);native_residual=decoder.decode_lapped(payload).samples;scalar_residual=decode_lapped_stream(payload).samples
                if not np.array_equal(native_residual,scalar_residual):raise RuntimeError("native/scalar Truth decode mismatch")
                residuals.append(native_residual)
            if not np.array_equal(residuals[0],residuals[1]) or not np.array_equal(residuals[0],truth.reconstruction):raise RuntimeError("full-pack Truth decode mismatch")
            final_sum=full_model.astype(np.int32)+residuals[0][:,0].astype(np.int32);clip_count=int(np.count_nonzero((final_sum<-32768)|(final_sum>32767)))
            if clip_count:rejections.append({"reason":"final_clip","count":clip_count});continue
            final=final_sum.astype(np.int16)[:,None];metrics=compute_metrics(frames,final,rate,("music",));public={k:v for k,v in proposal.items() if not k.startswith("_")};requirements=decoder.inspect_lapped(truth.payload);truth_ops=requirements.transform_frame_count*requirements.half_window*requirements.band_count+requirements.coefficient_elements+requirements.overlap_elements+requirements.output_elements;row={**public,"complete_bytes":len(pack),"baseline_bytes":len(baseline.payload),"imu_complete_bytes":len(direct),"imf_less_than_imu":len(pack)<len(direct),"eligible":eligible(metrics,baseline_metrics),"metrics":metrics,"pack_sha256":sha(pack),"imu_sha256":sha(direct),"residual_pcm_sha256":sha(residuals[0].astype("<i2",copy=False).tobytes()),"final_pcm_sha256":sha(final.astype("<i2",copy=False).tobytes()),"decode_operations":proposal["decode_operations"]+truth_ops,"preroll_samples":max(proposal["preroll_samples"],requirements.frame_count),"truth_encode_seconds":truth_seconds,"model_clip_count":0,"residual_clip_count":0,"final_clip_count":clip_count}
            stem=f"candidate-{len(rows):02d}-{row['pack_sha256'][:12]}";(case/f"{stem}.imf").write_bytes(pack);(case/f"{stem}.imu").write_bytes(direct);write_pcm16_channels(case/f"{stem}-decoded.wav",rate,final);rows.append(row)
    except (BoundFailure,MemoryError) as error:return capacity_fallback(error,proposer_evidence)
    except NativeCoreError as error:
        if error.status==6:return capacity_fallback(error,proposer_evidence)
        raise
    key=lambda x:(x["complete_bytes"],x["decode_operations"],x["preroll_samples"],x["modes"],x["pack_sha256"]);admissible=[x for x in rows if x["modes"]>=6 and x["eligible"] and x["imf_less_than_imu"] and x["complete_bytes"]<=.9*len(baseline.payload)];best=min(admissible,key=key) if admissible else None;rows.sort(key=lambda x:(not x["eligible"],*key(x)));model_pass=best is not None;passed=model_pass if require_model else True
    selected=best if model_pass else {"representation":"accepted-s12-fallback","complete_bytes":len(baseline.payload),"payload_sha256":sha(baseline.payload)}
    return {"status":"PASS" if passed else "FAIL","input_id":input_id,"selection":"model-on" if model_pass else "fallback","baseline_bytes":len(baseline.payload),"baseline_sha256":sha(baseline.payload),"baseline_metrics":baseline_metrics,"proposer_evidence":proposer_evidence,"candidates":rows,"rejections":rejections,"selected":selected,"wall_seconds":time.perf_counter()-started}

def peak_rss()->int:
    class Counters(ctypes.Structure):
        _fields_=[("cb",ctypes.c_uint32),("PageFaultCount",ctypes.c_uint32),("PeakWorkingSetSize",ctypes.c_size_t),("WorkingSetSize",ctypes.c_size_t),("QuotaPeakPagedPoolUsage",ctypes.c_size_t),("QuotaPagedPoolUsage",ctypes.c_size_t),("QuotaPeakNonPagedPoolUsage",ctypes.c_size_t),("QuotaNonPagedPoolUsage",ctypes.c_size_t),("PagefileUsage",ctypes.c_size_t),("PeakPagefileUsage",ctypes.c_size_t)]
    value=Counters();value.cb=ctypes.sizeof(value)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(),ctypes.byref(value),value.cb):raise RuntimeError("peak RSS query failed")
    return int(value.PeakWorkingSetSize)

def long_gate(core:Core,native_core:Path,out:Path,closure:Path,closure_sha:str,receipt_sha:str)->dict:
    wall=time.perf_counter();cpu=time.process_time();out.mkdir(parents=True,exist_ok=True);seal=validate_seal(native_core,closure,closure_sha,receipt_sha);p0_result=p0(core,False)
    holdout=evaluate_input(core,native_core,CONTROL/"p1-auditor-holdout-180s.wav","auditor-holdout",out,True)
    resource={"wall_seconds":time.perf_counter()-wall,"cpu_seconds":time.process_time()-cpu,"peak_rss_bytes":peak_rss(),"retained_bytes":sum(x.stat().st_size for x in out.rglob("*") if x.is_file())};resource["pass"]=resource["wall_seconds"]<=2400 and resource["cpu_seconds"]<=7200 and resource["peak_rss_bytes"]<=2<<30 and resource["retained_bytes"]<=512<<20
    report={"status":holdout["status"] if resource["pass"] else "FAIL","seal":seal,"p0":p0_result,"holdout":holdout,"holdout_resource":resource,"n1":"SUPPRESSED_AFTER_HOLDOUT_FAILURE_OR_RESOURCE_BOUND"}
    if report["status"]!="PASS":return report
    n1=evaluate_input(core,native_core,CONTROL/"n1-independent-drift-180s.wav","n1-independent-drift",out,False);report["n1"]=n1;report["status"]=n1["status"];return report

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--native-core",type=Path,required=True);parser.add_argument("--phase",choices=("p0","long"),required=True);parser.add_argument("--output",type=Path,default=ROOT/"artifacts/r271-s17-focused");parser.add_argument("--closure",type=Path);parser.add_argument("--closure-sha256");parser.add_argument("--receipt-sha256");args=parser.parse_args();wall=time.perf_counter();cpu=time.process_time();core=Core(args.native_core)
    if args.phase=="long" and not(args.closure and args.closure_sha256 and args.receipt_sha256):raise SystemExit("long phase requires sealed closure and receipt hashes")
    try:report=p0(core) if args.phase=="p0" else long_gate(core,args.native_core,args.output,args.closure,args.closure_sha256,args.receipt_sha256)
    except Exception as error:report={"status":"FAIL","failure_type":type(error).__name__,"failure":str(error)}
    report["wall_seconds"]=time.perf_counter()-wall;report["cpu_seconds"]=time.process_time()-cpu;report["peak_rss_bytes"]=peak_rss();report["retained_bytes"]=sum(x.stat().st_size for x in args.output.rglob("*") if x.is_file()) if args.output.exists() else 0
    ceiling=(2400,7200,2<<30,512<<20) if args.phase=="long" else (120,300,2<<30,64<<20);report["resource_ceiling"]={"wall_seconds":ceiling[0],"cpu_seconds":ceiling[1],"peak_rss_bytes":ceiling[2],"retained_bytes":ceiling[3]}
    if any(a>b for a,b in zip((report["wall_seconds"],report["cpu_seconds"],report["peak_rss_bytes"],report["retained_bytes"]),ceiling)):report["status"]="FAIL";report["resource_failure"]=True
    args.output.mkdir(parents=True,exist_ok=True);(args.output/f"{args.phase}-result.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,indent=2));return 0 if report["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
