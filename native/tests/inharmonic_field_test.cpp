#include "resonith/inharmonic_field.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <vector>

namespace {
void put16(std::vector<std::uint8_t>& b,std::size_t p,std::uint16_t v){b[p]=static_cast<std::uint8_t>(v);b[p+1]=static_cast<std::uint8_t>(v>>8U);}
void put32(std::vector<std::uint8_t>& b,std::size_t p,std::uint32_t v){for(unsigned i=0;i<4;++i)b[p+i]=static_cast<std::uint8_t>(v>>(8U*i));}
void put64(std::vector<std::uint8_t>& b,std::size_t p,std::uint64_t v){for(unsigned i=0;i<8;++i)b[p+i]=static_cast<std::uint8_t>(v>>(8U*i));}
std::uint32_t div_even(std::uint64_t n,std::uint64_t d){const auto q=n/d,r=n%d;return static_cast<std::uint32_t>(q+(r>d-r||(r==d-r&&(q&1U))));}

std::vector<std::uint8_t> imf(){
    std::vector<std::uint8_t> b(224U); std::copy_n("IMF1",4,b.begin()); b[4]=1; put16(b,6,96); put32(b,8,16000); put32(b,12,64);
    put16(b,16,1);put16(b,18,3);put16(b,20,1);put16(b,22,2);put64(b,32,96);put64(b,40,112);put64(b,48,160);
    put64(b,56,192);put64(b,64,224);put64(b,72,224);put64(b,80,192);
    put16(b,96,0);put16(b,98,0);put16(b,100,3);
    const std::array<std::uint32_t,3> ratios={1U<<20U,1572864U,2359296U}; const std::array<std::uint16_t,3> gains={2048,1024,512};
    for(std::size_t i=0;i<3;++i){const auto p=112U+16U*i;put32(b,p,ratios[i]);put32(b,p+4U,static_cast<std::uint32_t>(i)*0x12345678U);put16(b,p+8U,gains[i]);put32(b,p+12U,1U<<31U);}
    put16(b,160,0);put16(b,162,0);put16(b,164,2);put32(b,168,0);put32(b,172,64);
    const std::uint32_t step=26843546U;put32(b,192,0);put32(b,196,step);put16(b,200,32768);put32(b,208,64);put32(b,212,step);put16(b,216,32768);return b;
}
std::vector<std::uint8_t> imu(const std::vector<std::uint8_t>& source){
    std::vector<std::uint8_t> b(256U);std::copy_n("IMU1",4,b.begin());b[4]=1;put16(b,6,64);put32(b,8,16000);put32(b,12,64);
    put32(b,16,3);put32(b,20,6);put64(b,32,64);put64(b,40,160);put64(b,48,256);put64(b,56,256);
    for(std::size_t i=0;i<3;++i){const auto r=64U+32U*i,m=112U+16U*i;put32(b,r,0);put32(b,r+4U,64);put16(b,r+8U,static_cast<std::uint16_t>(2U*i));put16(b,r+10U,2);
        put16(b,r+12U,static_cast<std::uint16_t>(source[m+8U]|(source[m+9U]<<8U)));put32(b,r+16U,static_cast<std::uint32_t>(source[m+4U]|(source[m+5U]<<8U)|(source[m+6U]<<16U)|(source[m+7U]<<24U)));put32(b,r+20U,1U<<31U);
        const std::uint32_t ratio=static_cast<std::uint32_t>(source[m]|(source[m+1U]<<8U)|(source[m+2U]<<16U)|(source[m+3U]<<24U));const std::uint32_t step=div_even(26843546ULL*ratio,1U<<20U);
        for(std::size_t k=0;k<2;++k){const auto q=160U+16U*(2U*i+k);put32(b,q,k==0?0U:64U);put32(b,q+4U,step);put16(b,q+8U,32768);}}
    return b;
}
std::vector<std::uint8_t> two_basis(bool reverse){
    std::vector<std::uint8_t> b(352U);std::copy_n("IMF1",4,b.begin());b[4]=1;put16(b,6,96);put32(b,8,16000);put32(b,12,64);put16(b,16,2);put16(b,18,6);put16(b,20,2);put16(b,22,4);put64(b,32,96);put64(b,40,128);put64(b,48,224);put64(b,56,288);put64(b,64,352);put64(b,72,352);put64(b,80,384);
    for(std::size_t i=0;i<2;++i){put16(b,96U+16U*i,static_cast<std::uint16_t>(i));put16(b,98U+16U*i,static_cast<std::uint16_t>(3U*i));put16(b,100U+16U*i,3);}
    const std::array<std::uint32_t,3> ratios={1U<<20U,1572864U,2359296U};for(std::size_t i=0;i<6;++i){const auto p=128U+16U*i;put32(b,p,ratios[i%3]);put16(b,p+8U,1024);put32(b,p+12U,1U<<31U);}
    for(std::size_t i=0;i<2;++i){const auto p=224U+32U*i;put16(b,p,static_cast<std::uint16_t>(reverse?1U-i:i));put16(b,p+2U,static_cast<std::uint16_t>(2U*i));put16(b,p+4U,2);put32(b,p+8U,0);put32(b,p+12U,64);for(std::size_t k=0;k<2;++k){const auto q=288U+16U*(2U*i+k);put32(b,q,k?64U:0U);put32(b,q+4U,26843546U);put16(b,q+8U,32768);}}
    return b;
}
}

int main(){
    const auto a=imf();const auto d=imu(a);resonith_inharmonic_inspection info{};
    if(resonith_imf_inspect(a.data(),a.size(),&info)!=RESONITH_STATUS_OK||info.mode_samples!=192U)return 1;
    if(resonith_imu_inspect(d.data(),d.size(),&info)!=RESONITH_STATUS_OK||info.mode_samples!=192U)return 2;
    const std::array<std::int16_t,4> basis={32767,0,-32768,0};std::array<std::int16_t,64> x{},y{};
    resonith_maf_operation_budget bx{10000},by{10000};
    if(resonith_imf_render_model(a.data(),a.size(),basis.data(),basis.size(),x.data(),x.size(),&bx)!=RESONITH_STATUS_OK)return 3;
    if(resonith_imu_render_model(d.data(),d.size(),basis.data(),basis.size(),y.data(),y.size(),&by)!=RESONITH_STATUS_OK||x!=y)return 4;
    auto bad=a;bad[184]=1;if(resonith_imf_inspect(bad.data(),bad.size(),&info)==RESONITH_STATUS_OK)return 5;
    std::array<std::int16_t,64> sentinel{};sentinel.fill(1234);resonith_maf_operation_budget low{1};
    if(resonith_imf_render_model(a.data(),a.size(),basis.data(),basis.size(),sentinel.data(),sentinel.size(),&low)!=RESONITH_STATUS_PROFILE_BOUND
        ||!std::all_of(sentinel.begin(),sentinel.end(),[](std::int16_t v){return v==1234;}))return 6;
    sentinel.fill(1234);low.remaining=1;
    if(resonith_imu_render_model(d.data(),d.size(),basis.data(),basis.size(),sentinel.data(),sentinel.size(),&low)!=RESONITH_STATUS_PROFILE_BOUND
        ||!std::all_of(sentinel.begin(),sentinel.end(),[](std::int16_t v){return v==1234;})||low.remaining!=1U)return 7;
    auto clipped=a;for(std::size_t i=0;i<3;++i){put32(clipped,116U+16U*i,0);put16(clipped,120U+16U*i,32768);}std::array<std::int16_t,4> flat={32767,32767,32767,32767};sentinel.fill(1234);resonith_maf_operation_budget clip_budget{10000};
    if(resonith_imf_render_model(clipped.data(),clipped.size(),flat.data(),flat.size(),sentinel.data(),sentinel.size(),&clip_budget)!=RESONITH_STATUS_PROFILE_BOUND
        ||!std::all_of(sentinel.begin(),sentinel.end(),[](std::int16_t v){return v==1234;})||clip_budget.remaining!=10000U)return 8;
    auto huge=a;put32(huge,12,28800001U);if(resonith_imf_inspect(huge.data(),huge.size(),&info)!=RESONITH_STATUS_PROFILE_BOUND)return 9;
    const auto ordered=two_basis(false),reversed=two_basis(true);if(resonith_imf_inspect(ordered.data(),ordered.size(),&info)!=RESONITH_STATUS_OK||resonith_imf_inspect(reversed.data(),reversed.size(),&info)!=RESONITH_STATUS_MALFORMED)return 10;
    auto alias=a;resonith_maf_operation_budget alias_budget{10000};if(resonith_imf_render_model(alias.data(),alias.size(),basis.data(),basis.size(),reinterpret_cast<std::int16_t*>(alias.data()),64,&alias_budget)!=RESONITH_STATUS_INVALID_ARGUMENT||alias!=a||alias_budget.remaining!=10000U)return 11;
    auto direct_alias=d;alias_budget.remaining=10000;if(resonith_imu_render_model(direct_alias.data(),direct_alias.size(),basis.data(),basis.size(),reinterpret_cast<std::int16_t*>(direct_alias.data()),64,&alias_budget)!=RESONITH_STATUS_INVALID_ARGUMENT||direct_alias!=d||alias_budget.remaining!=10000U)return 12;
    const std::array<std::uint32_t,2> offsets={0,10},targets={1U<<27U,1U<<26U};std::uint32_t decay=0;std::uint64_t work=0;
    if(resonith_imf_fit_decay(2048,offsets.data(),targets.data(),2,&decay,&work)!=RESONITH_STATUS_OK||decay==0U||work==0U)return 13;
    return 0;
}
