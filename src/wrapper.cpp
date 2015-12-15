// Copyright (c) 2015, Dimitri Racordon.
// Licensed under the Apache License, Version 2.0.

#include <boost/python.hpp>

#include "types.hpp"
#include "ydd.hpp"


BOOST_PYTHON_MODULE(_cpp) {
    using namespace boost::python;

    using szt = std::size_t;

    using IntEngine = ydd::Engine<int>;
    using IntRoot = IntEngine::Root;

    class_<IntRoot>("IntRoot", init<>())
        // When the keys are defined with a primitive type (int, float, ...),
        // using the return policy `return_internal_reference` seems to make
        // Boost complain about a missing function to call `assertion_failed`.
        .add_property("key", make_function(
            &IntRoot::key, return_value_policy<copy_const_reference>()))

        // Since `then_` and `else_` return references, we need to tell Boost
        // how to handle them. Using `return_internal_reference`, we specify
        // that the returned reference is held by the `Root` instance.
        .add_property("then_", make_function(
            &IntRoot::then_, return_internal_reference<>()))
        .add_property("else_", make_function(
            &IntRoot::else_, return_internal_reference<>()))

        .def(self < self)
        .def(self <= self)
        .def(self == self)
        .def(self != self)
        .def(self | self)
        .def(self & self)
        .def(self - self)
        .def(self ^ self)

        .def("is_one", &IntRoot::is_one)
        .def("is_zero", &IntRoot::is_zero)
        .def("__len__", &IntRoot::size)
        .def("__hash__", &IntRoot::hash);

    class_<IntEngine, boost::noncopyable>(
        "IntEngine", init<optional<szt, szt, szt, szt, szt, szt>>((
            arg("bucket_count"),
            arg("bucket_size"),
            arg("union_cache_size"),
            arg("intersection_cache_size"),
            arg("difference_cache_size"),
            arg("symmetric_difference_cache_size"))))

        .def_readonly("bucket_count", &IntEngine::bucket_count)
        .def_readonly("bucket_size", &IntEngine::bucket_size)

        .def("make_terminal", &IntEngine::make_terminal)
        .def("make_node", &IntEngine::make_node);


    using PNEngine = ydd::Engine<ydd::PNPlace>;
    using PNRoot = PNEngine::Root;

    class_<ydd::PNPlace>(
        "PNPlace", init<szt, optional<szt>>((arg("id_"), arg("tokens"))))
        .def_readonly("id_", &ydd::PNPlace::id_)
        .def_readwrite("tokens", &ydd::PNPlace::tokens)
        .def(self < self)
        .def(self == self)
        .def(self > self)
        .def("__hash__", &ydd::PNPlace::hash);

    class_<PNRoot>("PNRoot", init<>())
        .add_property("key", make_function(
            &PNRoot::key, return_internal_reference<>()))
        .add_property("then_", make_function(
            &PNRoot::then_, return_internal_reference<>()))
        .add_property("else_", make_function(
            &PNRoot::else_, return_internal_reference<>()))

        .def(self < self)
        .def(self <= self)
        .def(self == self)
        .def(self != self)
        .def(self | self)
        .def(self & self)
        .def(self - self)
        .def(self ^ self)

        .def("is_one", &PNRoot::is_one)
        .def("is_zero", &PNRoot::is_zero)
        .def("__len__", &PNRoot::size)
        .def("__hash__", &PNRoot::hash);

    class_<PNEngine, boost::noncopyable>(
        "PNEngine", init<optional<szt, szt, szt, szt, szt, szt>>((
            arg("bucket_count"),
            arg("bucket_size"),
            arg("union_cache_size"),
            arg("intersection_cache_size"),
            arg("difference_cache_size"),
            arg("symmetric_difference_cache_size"))))

        .def_readonly("bucket_count", &PNEngine::bucket_count)
        .def_readonly("bucket_size", &PNEngine::bucket_size)

        .def("make_terminal", &PNEngine::make_terminal)
        .def("make_node", &PNEngine::make_node);

}
