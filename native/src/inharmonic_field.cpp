#include "resonith/inharmonic_field.h"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace {

constexpr std::uint64_t kMaxBytes = 268435456ULL;
constexpr std::uint64_t kMaxModeSamples = 150000000ULL;
constexpr std::uint32_t kMaxSamples = 28800000U;

std::uint16_t u16(const std::uint8_t* p) noexcept {
    return static_cast<std::uint16_t>(p[0] | (static_cast<std::uint16_t>(p[1]) << 8U));
}
std::uint32_t u32(const std::uint8_t* p) noexcept {
    return static_cast<std::uint32_t>(p[0]) | (static_cast<std::uint32_t>(p[1]) << 8U)
        | (static_cast<std::uint32_t>(p[2]) << 16U) | (static_cast<std::uint32_t>(p[3]) << 24U);
}
std::uint64_t u64(const std::uint8_t* p) noexcept {
    return u32(p) | (static_cast<std::uint64_t>(u32(p + 4U)) << 32U);
}
bool add(std::uint64_t a, std::uint64_t b, std::uint64_t& out) noexcept {
    if (b > std::numeric_limits<std::uint64_t>::max() - a) return false;
    out = a + b; return true;
}
bool mul(std::uint64_t a, std::uint64_t b, std::uint64_t& out) noexcept {
    if (a != 0U && b > std::numeric_limits<std::uint64_t>::max() / a) return false;
    out = a * b; return true;
}
bool overlap(const void* a,std::size_t an,const void* b,std::size_t bn) noexcept {
    if(an==0U||bn==0U)return false;const auto ap=reinterpret_cast<std::uintptr_t>(a),bp=reinterpret_cast<std::uintptr_t>(b),limit=std::numeric_limits<std::uintptr_t>::max();
    if(an>limit-ap||bn>limit-bp)return true;return ap<bp+bn&&bp<ap+an;
}
std::uint64_t round_even_u(std::uint64_t n, std::uint64_t d) noexcept {
    const std::uint64_t q = n / d, r = n % d;
    return q + static_cast<std::uint64_t>(r > d - r || (r == d - r && (q & 1U) != 0U));
}
std::int64_t round_even_s(std::int64_t n, std::int64_t d) noexcept {
    const bool neg = n < 0; const std::uint64_t mag = neg
        ? static_cast<std::uint64_t>(-(n + 1)) + 1U : static_cast<std::uint64_t>(n);
    const std::int64_t q = static_cast<std::int64_t>(round_even_u(mag, static_cast<std::uint64_t>(d)));
    return neg ? -q : q;
}
std::int64_t round_product3_away_s(std::int64_t signed_a, std::uint32_t b,
                                   std::uint32_t c, std::uint64_t d) noexcept {
    const bool negative = signed_a < 0;
    const std::uint64_t a = negative
        ? static_cast<std::uint64_t>(-(signed_a + 1)) + 1U
        : static_cast<std::uint64_t>(signed_a);
    const std::uint64_t ab = a * b;
    const std::uint64_t quotient = ab / d;
    const std::uint64_t remainder = ab % d;
    const std::uint64_t tail = remainder * c;
    const std::uint64_t magnitude = quotient * c + tail / d
        + static_cast<std::uint64_t>((tail % d) * 2U >= d);
    const auto value = static_cast<std::int64_t>(magnitude);
    return negative ? -value : value;
}

struct Parsed {
    bool direct{}; std::uint32_t rate{}, samples{}, bases{}, modes{}, instances{}, knots{}, truth{};
    std::uint64_t basis_off{}, mode_off{}, instance_off{}, knot_off{}, truth_off{}, bytes{}, mode_samples{};
};

resonith_status basic(const std::uint8_t* data, std::size_t size, const char magic[4],
                      std::uint16_t header) noexcept {
    if (data == nullptr) return RESONITH_STATUS_INVALID_ARGUMENT;
    if (size < header) return RESONITH_STATUS_TRUNCATED;
    if (!std::equal(magic, magic + 4, data)) return RESONITH_STATUS_BAD_MAGIC;
    if (data[4] != 1U || data[5] != 0U) return RESONITH_STATUS_UNSUPPORTED_VERSION;
    if (u16(data + 6U) != header) return RESONITH_STATUS_MALFORMED;
    return RESONITH_STATUS_OK;
}

resonith_status parse_imf(const std::uint8_t* data, std::size_t size, Parsed& h) noexcept {
    const char magic[4] = {'I','M','F','1'}; resonith_status s = basic(data, size, magic, 96U);
    if (s != RESONITH_STATUS_OK) return s;
    h.rate=u32(data+8U); h.samples=u32(data+12U); h.bases=u16(data+16U); h.modes=u16(data+18U);
    h.instances=u16(data+20U); h.knots=u16(data+22U); h.truth=u32(data+24U);
    h.basis_off=u64(data+32U); h.mode_off=u64(data+40U); h.instance_off=u64(data+48U);
    h.knot_off=u64(data+56U); h.truth_off=u64(data+64U); h.bytes=u64(data+72U);
    const std::uint64_t declared_mode_samples=u64(data+80U);
    if (u32(data+28U)!=0U || u64(data+88U)!=0U || h.rate<8000U || h.rate>48000U
        || h.samples==0U || h.samples>kMaxSamples || h.bases==0U || h.bases>RESONITH_IMF_MAX_BASES
        || h.modes<3U || h.modes>RESONITH_IMF_MAX_MODES || h.instances==0U
        || h.instances>RESONITH_IMF_MAX_INSTANCES || h.knots<2U || h.knots>RESONITH_IMF_MAX_KNOTS
        || h.truth>kMaxBytes || h.bytes!=size || h.bytes>kMaxBytes) return RESONITH_STATUS_PROFILE_BOUND;
    std::uint64_t p=96U, n=0U;
    if (h.basis_off!=p || !mul(h.bases,16U,n) || !add(p,n,p) || h.mode_off!=p
        || !mul(h.modes,16U,n) || !add(p,n,p) || h.instance_off!=p
        || !mul(h.instances,32U,n) || !add(p,n,p) || h.knot_off!=p
        || !mul(h.knots,16U,n) || !add(p,n,p) || h.truth_off!=p
        || !add(p,h.truth,p) || p!=h.bytes) return p>size?RESONITH_STATUS_TRUNCATED:RESONITH_STATUS_MALFORMED;
    std::uint32_t next_mode=0U;
    for (std::uint32_t i=0;i<h.bases;++i) {
        const std::uint8_t* b=data+h.basis_off+16ULL*i; const std::uint32_t first=u16(b+2U), count=u16(b+4U);
        if (u16(b)!=i || first!=next_mode || count<3U || count>16U || u16(b+6U)!=0U || u64(b+8U)!=0U
            || count>h.modes-next_mode) return RESONITH_STATUS_MALFORMED;
        std::uint32_t previous=0U;
        for (std::uint32_t k=0;k<count;++k) {
            const std::uint8_t* m=data+h.mode_off+16ULL*(first+k); const std::uint32_t ratio=u32(m);
            if ((k==0U?ratio!=(1U<<20U):ratio<=previous) || u16(m+10U)!=0U
                || u16(m+8U)>32768U || u32(m+12U)>(1U<<31U)) return RESONITH_STATUS_MALFORMED;
            previous=ratio;
        }
        next_mode+=count;
    }
    if (next_mode!=h.modes) return RESONITH_STATUS_MALFORMED;
    std::uint32_t next_knot=0U, last_start=0U, last_basis=0U, last_first_knot=0U;
    bool first_instance=true; std::uint64_t mode_samples=0U;
    for (std::uint32_t i=0;i<h.instances;++i) {
        const std::uint8_t* x=data+h.instance_off+32ULL*i; const std::uint32_t basis=u16(x), fk=u16(x+2U), kc=u16(x+4U);
        const std::uint32_t start=u32(x+8U), duration=u32(x+12U);
        if (basis>=h.bases || fk!=next_knot || kc<2U || kc>RESONITH_IMF_MAX_KNOTS_PER_INSTANCE
            || u16(x+6U)!=0U || u32(x+20U)!=0U || u64(x+24U)!=0U || duration==0U
            || start>=h.samples || duration>h.samples-start
            || (!first_instance && (start<last_start || (start==last_start && (basis<last_basis
                || (basis==last_basis && fk<last_first_knot)))))) return RESONITH_STATUS_MALFORMED;
        first_instance=false; last_start=start; last_basis=basis; last_first_knot=fk;
        const std::uint8_t* b=data+h.basis_off+16ULL*basis;
        const std::uint32_t mode_count=u16(b+4U); std::uint64_t work=0U;
        if (!mul(duration,mode_count,work) || !add(mode_samples,work,mode_samples)) return RESONITH_STATUS_PROFILE_BOUND;
        std::uint32_t previous=0U;
        for (std::uint32_t k=0;k<kc;++k) {
            const std::uint8_t* q=data+h.knot_off+16ULL*(fk+k); const std::uint32_t offset=u32(q), step=u32(q+4U);
            if ((k==0U?offset!=0U:offset<=previous)
                || (k+1U==kc?offset!=duration:offset>=duration) || step>=(1U<<31U)
                || u16(q+8U)>32768U || u16(q+10U)!=0U || u32(q+12U)!=0U) return RESONITH_STATUS_MALFORMED;
            for (std::uint32_t m=0;m<mode_count;++m) {
                const std::uint32_t ratio=u32(data+h.mode_off+16ULL*(u16(b+2U)+m));
                if (round_even_u(static_cast<std::uint64_t>(step)*ratio,1U<<20U)>=(1ULL<<31U)) return RESONITH_STATUS_PROFILE_BOUND;
            }
            previous=offset;
        }
        next_knot+=kc;
    }
    if (next_knot!=h.knots || mode_samples!=declared_mode_samples) return RESONITH_STATUS_MALFORMED;
    if (mode_samples>kMaxModeSamples) return RESONITH_STATUS_PROFILE_BOUND;
    for (std::uint32_t i=0;i<h.instances;++i) {
        const std::uint8_t* a=data+h.instance_off+32ULL*i; std::uint32_t active=0U, start=u32(a+8U);
        for (std::uint32_t j=0;j<h.instances;++j) { const std::uint8_t* b=data+h.instance_off+32ULL*j;
            if (u32(b+8U)<=start && start-u32(b+8U)<u32(b+12U)) active+=u16(data+h.basis_off+16ULL*u16(b)+4U); }
        if (active>RESONITH_IMF_MAX_MODES) return RESONITH_STATUS_PROFILE_BOUND;
    }
    h.mode_samples=mode_samples; return RESONITH_STATUS_OK;
}

resonith_status parse_imu(const std::uint8_t* data, std::size_t size, Parsed& h) noexcept {
    const char magic[4]={'I','M','U','1'}; resonith_status s=basic(data,size,magic,64U); if(s!=RESONITH_STATUS_OK)return s;
    h.direct=true; h.rate=u32(data+8U); h.samples=u32(data+12U); h.instances=u32(data+16U); h.modes=h.instances;
    h.knots=u32(data+20U); h.truth=u32(data+24U); h.instance_off=u64(data+32U); h.knot_off=u64(data+40U);
    h.truth_off=u64(data+48U); h.bytes=u64(data+56U);
    if(u32(data+28U)!=0U || h.rate<8000U || h.rate>48000U || h.samples==0U || h.samples>kMaxSamples
        || h.instances==0U || h.instances>RESONITH_IMU_MAX_RECORDS || h.knots<2U || h.knots>RESONITH_IMU_MAX_KNOTS
        || h.truth>kMaxBytes || h.bytes!=size || h.bytes>kMaxBytes) return RESONITH_STATUS_PROFILE_BOUND;
    std::uint64_t p=64U,n=0U; if(h.instance_off!=p || !mul(h.instances,32U,n) || !add(p,n,p) || h.knot_off!=p
        || !mul(h.knots,16U,n) || !add(p,n,p) || h.truth_off!=p || !add(p,h.truth,p) || p!=h.bytes)
        return p>size?RESONITH_STATUS_TRUNCATED:RESONITH_STATUS_MALFORMED;
    std::uint32_t next=0U,last_start=0U; bool first=true; std::uint64_t work=0U;
    for(std::uint32_t i=0;i<h.instances;++i){const std::uint8_t* x=data+h.instance_off+32ULL*i; const std::uint32_t start=u32(x),dur=u32(x+4U),fk=u16(x+8U),kc=u16(x+10U);
        if(fk!=next || kc<2U || kc>RESONITH_IMF_MAX_KNOTS_PER_INSTANCE || u16(x+14U)!=0U || u64(x+24U)!=0U
            || u16(x+12U)>32768U || u32(x+20U)>(1U<<31U) || dur==0U || start>=h.samples || dur>h.samples-start
            || (!first&&start<last_start)) return RESONITH_STATUS_MALFORMED;
        first=false; last_start=start;
        std::uint32_t previous=0U; for(std::uint32_t k=0;k<kc;++k){const std::uint8_t* q=data+h.knot_off+16ULL*(fk+k); const std::uint32_t off=u32(q);
            if((k==0U?off!=0U:off<=previous) || (k+1U==kc?off!=dur:off>=dur)
                || u32(q+4U)>=(1U<<31U) || u16(q+8U)>32768U || u16(q+10U)!=0U || u32(q+12U)!=0U) return RESONITH_STATUS_MALFORMED;
            previous=off;}
        next+=kc; if(!add(work,dur,work))return RESONITH_STATUS_PROFILE_BOUND; }
    if(next!=h.knots)return RESONITH_STATUS_MALFORMED;
    if(work>kMaxModeSamples)return RESONITH_STATUS_PROFILE_BOUND;
    for(std::uint32_t i=0;i<h.instances;++i){const std::uint8_t* a=data+h.instance_off+32ULL*i; std::uint32_t active=0U,start=u32(a);
        for(std::uint32_t j=0;j<h.instances;++j){const std::uint8_t* b=data+h.instance_off+32ULL*j; if(u32(b)<=start&&start-u32(b)<u32(b+4U))++active;}
        if(active>RESONITH_IMF_MAX_MODES)return RESONITH_STATUS_PROFILE_BOUND;}
    h.mode_samples=work; return RESONITH_STATUS_OK;
}

struct View { std::uint32_t start{},duration{},first_knot{},knot_count{},ratio{1U<<20U},phase{},decay{},relative{}; };
std::uint32_t step_at(const std::uint8_t* data,const Parsed& h,const View& v,std::uint32_t k) noexcept {
    const std::uint32_t step=u32(data+h.knot_off+16ULL*(v.first_knot+k)+4U);
    return h.direct?step:static_cast<std::uint32_t>(round_even_u(static_cast<std::uint64_t>(step)*v.ratio,1U<<20U));
}
std::uint32_t gain_at(const std::uint8_t* data,const Parsed& h,const View& v,std::uint32_t p,std::uint32_t interval) noexcept {
    const std::uint8_t* a=data+h.knot_off+16ULL*(v.first_knot+interval); const std::uint8_t* b=a+16U;
    const std::uint32_t x=u32(a),d=u32(b)-x; const std::int64_t delta=static_cast<std::int64_t>(u16(b+8U))-u16(a+8U);
    return static_cast<std::uint32_t>(static_cast<std::int64_t>(u16(a+8U))+round_even_s(delta*(p-x),d));
}
std::int64_t phase_advance(std::uint32_t n,std::uint32_t a,std::uint32_t b) noexcept {
    const std::int64_t delta=static_cast<std::int64_t>(b)-a;
    return static_cast<std::int64_t>(n)*a
        + round_product3_away_s(delta,n,n-1U,2ULL*n);
}
std::uint32_t phase_at(std::uint32_t origin,std::uint32_t local,std::uint32_t length,std::uint32_t a,std::uint32_t b) noexcept {
    const std::int64_t delta=static_cast<std::int64_t>(b)-a;
    return static_cast<std::uint32_t>(origin+static_cast<std::int64_t>(local)*a
        +round_product3_away_s(delta,local,local-1U,2ULL*length));
}
std::int16_t periodic(const std::int16_t* basis,std::size_t count,std::uint32_t phase) noexcept {
    const std::uint64_t pos=static_cast<std::uint64_t>(phase)*count; const std::size_t left=static_cast<std::size_t>(pos>>32U),right=left+1U==count?0U:left+1U;
    const std::int64_t fraction=static_cast<std::int64_t>((pos>>16U)&0xffffU), weighted=static_cast<std::int64_t>(basis[left])*(65536-fraction)+static_cast<std::int64_t>(basis[right])*fraction+32768;
    const std::int64_t value=weighted>=0?weighted/65536:-((-weighted+65535)/65536); return static_cast<std::int16_t>(std::clamp<std::int64_t>(value,-32768,32767));
}
struct Active { View view{}; std::uint32_t interval{},origin{}; std::uint64_t decay_state{}; bool used{}; };

resonith_status build_views(const std::uint8_t* data,const Parsed& h,std::array<View,RESONITH_IMU_MAX_RECORDS>& views,std::uint32_t& count) noexcept {
    count=0U; if(h.direct){for(std::uint32_t i=0;i<h.instances;++i){const std::uint8_t* x=data+h.instance_off+32ULL*i;
        views[count++]={u32(x),u32(x+4U),u16(x+8U),u16(x+10U),1U<<20U,u32(x+16U),u32(x+20U),u16(x+12U)};} return RESONITH_STATUS_OK;}
    for(std::uint32_t i=0;i<h.instances;++i){const std::uint8_t* x=data+h.instance_off+32ULL*i; const std::uint8_t* b=data+h.basis_off+16ULL*u16(x);
        for(std::uint32_t m=0;m<u16(b+4U);++m){const std::uint8_t* q=data+h.mode_off+16ULL*(u16(b+2U)+m); const std::uint32_t ratio=u32(q);
            const std::uint32_t folded=u32(q+4U)+static_cast<std::uint32_t>(round_even_u(static_cast<std::uint64_t>(u32(x+16U))*ratio,1U<<20U));
            views[count++]={u32(x+8U),u32(x+12U),u16(x+2U),u16(x+4U),ratio,folded,u32(q+12U),u16(q+8U)};}}
    return RESONITH_STATUS_OK;
}

resonith_status render_pass(const std::uint8_t* data,const Parsed& h,const std::array<View,RESONITH_IMU_MAX_RECORDS>& views,
                            std::uint32_t view_count,const std::int16_t* basis,std::size_t basis_count,std::int16_t* output,bool write) noexcept {
    std::array<Active,RESONITH_IMF_MAX_MODES> active{}; std::uint32_t next=0U;
    for(std::uint32_t sample=0;sample<h.samples;++sample){for(auto& a:active)if(a.used&&sample-a.view.start>=a.view.duration)a.used=false;
        while(next<view_count&&views[next].start==sample){auto slot=std::find_if(active.begin(),active.end(),[](const Active& a){return !a.used;}); if(slot==active.end())return RESONITH_STATUS_PROFILE_BOUND;
            *slot={views[next],0U,views[next].phase,static_cast<std::uint64_t>(views[next].relative)<<16U,true}; ++next;}
        std::int64_t total=0; for(auto& a:active)if(a.used){const std::uint32_t local=sample-a.view.start;
            while(a.interval+1U<a.view.knot_count-1U&&local>=u32(data+h.knot_off+16ULL*(a.view.first_knot+a.interval+1U))){const std::uint32_t x=u32(data+h.knot_off+16ULL*(a.view.first_knot+a.interval));
                const std::uint32_t y=u32(data+h.knot_off+16ULL*(a.view.first_knot+a.interval+1U)); a.origin+=static_cast<std::uint32_t>(phase_advance(y-x,step_at(data,h,a.view,a.interval),step_at(data,h,a.view,a.interval+1U))); ++a.interval;}
            const std::uint32_t x=u32(data+h.knot_off+16ULL*(a.view.first_knot+a.interval)),y=u32(data+h.knot_off+16ULL*(a.view.first_knot+a.interval+1U));
            const std::uint32_t ph=phase_at(a.origin,local-x,y-x,step_at(data,h,a.view,a.interval),step_at(data,h,a.view,a.interval+1U));
            const std::int64_t product=static_cast<std::int64_t>(periodic(basis,basis_count,ph))*static_cast<std::int64_t>(a.decay_state)*gain_at(data,h,a.view,local,a.interval);
            total+=round_even_s(product,1LL<<46U); a.decay_state=round_even_u(a.decay_state*a.view.decay,1ULL<<31U);}
        if(total<-32768 || total>32767)return RESONITH_STATUS_PROFILE_BOUND; if(write)output[sample]=static_cast<std::int16_t>(total);}
    return next==view_count?RESONITH_STATUS_OK:RESONITH_STATUS_MALFORMED;
}

resonith_status inspect_common(const std::uint8_t* data,std::size_t size,bool direct,resonith_inharmonic_inspection* out,Parsed* parsed) noexcept {
    if(out==nullptr)return RESONITH_STATUS_INVALID_ARGUMENT; *out={}; Parsed h{}; const resonith_status s=direct?parse_imu(data,size,h):parse_imf(data,size,h); if(s!=RESONITH_STATUS_OK)return s;
    out->sample_rate=h.rate; out->sample_count=h.samples; out->basis_count=h.bases; out->mode_count=h.modes; out->instance_count=h.instances;
    out->knot_count=h.knots; out->truth_bytes=h.truth; out->truth_offset=h.truth_off; out->complete_bytes=h.bytes; out->mode_samples=h.mode_samples; if(parsed!=nullptr)*parsed=h; return RESONITH_STATUS_OK;
}
resonith_status render(const std::uint8_t* data,std::size_t size,bool direct,const std::int16_t* basis,std::size_t basis_count,
                       std::int16_t* output,std::size_t capacity,resonith_maf_operation_budget* budget) noexcept {
    if(basis==nullptr||basis_count<2U||basis_count>16384U||output==nullptr||budget==nullptr)return RESONITH_STATUS_INVALID_ARGUMENT;
    resonith_inharmonic_inspection info{}; Parsed h{}; resonith_status s=inspect_common(data,size,direct,&info,&h); if(s!=RESONITH_STATUS_OK)return s;
    if(capacity<h.samples)return RESONITH_STATUS_OUTPUT_TOO_SMALL; const std::size_t output_bytes=static_cast<std::size_t>(h.samples)*sizeof(std::int16_t),basis_bytes=basis_count*sizeof(std::int16_t);
    if(overlap(output,output_bytes,data,size)||overlap(output,output_bytes,basis,basis_bytes)||overlap(output,output_bytes,budget,sizeof(*budget))||overlap(budget,sizeof(*budget),data,size)||overlap(budget,sizeof(*budget),basis,basis_bytes))return RESONITH_STATUS_INVALID_ARGUMENT;
    std::uint64_t required=0U; if(!mul(h.mode_samples,2U,required)||!add(required,h.samples*2ULL,required)||budget->remaining<required)return RESONITH_STATUS_PROFILE_BOUND;
    std::array<View,RESONITH_IMU_MAX_RECORDS> views{}; std::uint32_t count=0U; s=build_views(data,h,views,count); if(s!=RESONITH_STATUS_OK)return s;
    s=render_pass(data,h,views,count,basis,basis_count,nullptr,false); if(s!=RESONITH_STATUS_OK)return s;
    s=render_pass(data,h,views,count,basis,basis_count,output,true); if(s==RESONITH_STATUS_OK)budget->remaining-=required; return s;
}
} // namespace

extern "C" resonith_status resonith_imf_inspect(const std::uint8_t* d,std::size_t n,resonith_inharmonic_inspection* i){return inspect_common(d,n,false,i,nullptr);}
extern "C" resonith_status resonith_imu_inspect(const std::uint8_t* d,std::size_t n,resonith_inharmonic_inspection* i){return inspect_common(d,n,true,i,nullptr);}
extern "C" resonith_status resonith_imf_render_model(const std::uint8_t* d,std::size_t n,const std::int16_t* b,std::size_t bc,std::int16_t* o,std::size_t oc,resonith_maf_operation_budget* w){return render(d,n,false,b,bc,o,oc,w);}
extern "C" resonith_status resonith_imu_render_model(const std::uint8_t* d,std::size_t n,const std::int16_t* b,std::size_t bc,std::int16_t* o,std::size_t oc,resonith_maf_operation_budget* w){return render(d,n,true,b,bc,o,oc,w);}
extern "C" resonith_status resonith_imf_fit_decay(std::uint16_t relative,const std::uint32_t* offsets,const std::uint32_t* targets,std::size_t count,std::uint32_t* result,std::uint64_t* work){
    if(offsets==nullptr||targets==nullptr||result==nullptr||work==nullptr)return RESONITH_STATUS_INVALID_ARGUMENT; *result=0U;*work=0U;
    if(relative==0U||count<2U||count>RESONITH_IMF_MAX_KNOTS_PER_INSTANCE||offsets[0]!=0U||offsets[count-1U]>kMaxSamples)return RESONITH_STATUS_PROFILE_BOUND;
    for(std::size_t i=0;i<count;++i)if((i!=0U&&offsets[i]<=offsets[i-1U])||targets[i]>(1U<<31U))return RESONITH_STATUS_MALFORMED;
    const auto passes=[&](std::uint32_t decay){std::uint64_t state=static_cast<std::uint64_t>(relative)<<16U;std::size_t knot=0U;
        for(std::uint32_t p=0;;++p){if(p==offsets[knot]){++*work;if(state>static_cast<std::uint64_t>(targets[knot])+65535U)return false;if(++knot==count)return true;}
            state=round_even_u(state*decay,1ULL<<31U);++*work;}};
    if(passes(1U<<31U)){*result=1U<<31U;return RESONITH_STATUS_OK;} if(!passes(0U))return RESONITH_STATUS_NOT_FOUND;
    std::uint32_t accepted=0U;for(int bit=30;bit>=0;--bit){const std::uint32_t candidate=accepted|(1U<<static_cast<unsigned>(bit));if(passes(candidate))accepted=candidate;}
    *result=accepted;return RESONITH_STATUS_OK;
}
