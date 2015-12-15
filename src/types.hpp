// Copyright (c) 2015, Dimitri Racordon.
// Licensed under the Apache License, Version 2.0.

#ifndef __cppydd_types__
#define __cppydd_types__

#include <boost/functional/hash.hpp>


namespace ydd {

    struct PNPlace {
        PNPlace(std::size_t id_=0, std::size_t tokens=0) : id_(id_), tokens(tokens) {}

        bool operator< (const PNPlace& other) const {
            if (this->id_ == other.id_) {
                return this->tokens < other.tokens;
            } else {
                return this->id_ < other.id_;
            }
        }

        bool operator== (const PNPlace& other) const {
            return (this->id_ == other.id_) and (this->tokens == other.tokens);
        }

        bool operator> (const PNPlace& other) const {
            if (this->id_ == other.id_) {
                return this->tokens > other.tokens;
            } else {
                return this->id_ > other.id_;
            }
        }

        std::size_t hash() const {
            std::hash<std::size_t> hasher;

            std::size_t rv = 0;
            boost::hash_combine(rv, hasher(this->id_));
            boost::hash_combine(rv, hasher(this->tokens));
            return rv;
        }

        std::size_t id_;
        std::size_t tokens;
    };

}


namespace std {

    template<> struct hash<ydd::PNPlace> {
        std::size_t operator() (const ydd::PNPlace& place) const {
            return place.hash();
        }
    };

}

#endif
