//  Copyright Joel de Guzman 2002-2004. Distributed under the Boost
//  Software License, Version 1.0. (See accompanying file LICENSE_1_0.txt
//  or copy at http://www.boost.org/LICENSE_1_0.txt)
//  Hello World Example from the tutorial
//  [Joel de Guzman 10/9/2002]

#include <boost/python.hpp>

#include "ydd.hpp"


struct Config {
    using Key = int;
    static const std::size_t buckets_nb = 8000;
    static const std::size_t union_cache_size = 80;
    static const std::size_t intersection_cache_size = 80;
    static const std::size_t difference_cache_size = 80;
    static const std::size_t symmetric_difference_cache_size = 80;
};


BOOST_PYTHON_MODULE(_cpp) {
    using namespace boost::python;

    using IntEngine = ydd::Engine<Config>;
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

    class_<IntEngine, boost::noncopyable>("IntEngine", init<>())
        .def("make_terminal", &IntEngine::make_terminal)
        .def("make_node", &IntEngine::make_node);
}
