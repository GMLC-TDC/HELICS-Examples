#ifndef TOM_COMMON_HPP__
#define TOM_COMMON_HPP__

#include <helics/application_api/ValueFederate.hpp>

template <typename T>
struct ValuePacket
{
    helics::Time time_;
    helics::Publication &pub_;
    T value_;

    ValuePacket () = default;
    ValuePacket (helics::Time time, helics::Publication &pub, T value) : time_{time}, pub_{pub}, value_{value} {}
};  // struct ValuePacket

#endif /* TOM_COMMON_HPP__ */

