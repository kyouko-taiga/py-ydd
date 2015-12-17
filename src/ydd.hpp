// Copyright (c) 2015, Dimitri Racordon.
// Licensed under the Apache License, Version 2.0.

#ifndef __cppydd_ydd__
#define __cppydd_ydd__

#include <functional>
#include <stdexcept>
#include <unordered_set>

#include <boost/functional/hash.hpp>


namespace ydd {

    template <typename Key>
    class Engine {
    private:
        class Node;

    public:
        class Root {
        private:
            Engine* _engine;

        public:
            Root()
            : _engine(nullptr), node(nullptr) {
            }

            Root(const Root& other)
            : _engine(other._engine), node(other.node) {
                if (this->node != nullptr) {
                    this->node->ref_count++;
                }
            }

            Root(Engine& engine, const Node* node)
            : _engine(&engine), node(node) {
                this->node->ref_count++;
            }

            ~Root() {
                if (this->node != nullptr) {
                    this->node->ref_count--;
                    if (this->node->ref_count == 0) {
                        this->_engine->_unique_table.destroy_node(this->node);
                        this->node = nullptr;
                    }
                }
            }

            Root& operator= (const Root& other) {
                if (this->node != nullptr) {
                    this->node->ref_count--;
                    if (this->node->ref_count == 0) {
                        this->_engine->_unique_table.destroy_node(this->node);
                        this->node = nullptr;
                    }
                }

                this->node = other.node;
                this->_engine = other._engine;

                if (this->node != nullptr) {
                    this->node->ref_count++;
                }
                return *this;
            }

            bool operator< (const Root& other) const {
                if (this->is_zero()) {
                    return !other.is_zero();
                }

                if (other.is_zero() or other.is_one()) {
                    return false;
                }

                if (this->is_one()) {
                    return *this <= other.else_();
                }

                if (other.key() > this->key()) {
                    return false;
                } else if (other.key() == this->key()) {
                    return
                        (*this != other)
                        and (this->then_() <= other.then_())
                        and (this->else_() <= other.else_());
                } else {
                    return *this < other.else_();
                }
            }

            bool operator<= (const Root& other) const {
                if (this->is_zero()) {
                    return true;
                }

                if (other.is_zero() or other.is_one()) {
                    return *this == other;
                }

                if (this->is_one()) {
                    return *this <= other.else_();
                }

                if (other.key() > this->key()) {
                    return false;
                } else if (other.key() == this->key()) {
                    return
                        (*this == other)
                        or ((this->then_() <= other.then_()) and (this->else_() <= other.else_()));
                } else {
                    return *this <= other.else_();
                }
            }

            bool operator== (const Root& other) const {
                return this->node == other.node;
            }

            bool operator!= (const Root& other) const {
                return this->node != other.node;
            }

            Root operator| (const Root& other) const {
                if (this->is_zero()) {
                    return other;
                } else if (other.is_zero()) {
                    return *this;
                }

                // Try to get the result from the cache.
                auto& cache_record = this->_engine->_union_cache(*this, other);
                if ((cache_record.left == *this) and (cache_record.right == other)) {
                    return cache_record.result;
                }

                // Compute the result.
                Root rv;

                if (this->is_one()) {
                    if (other.is_one() or other.is_zero()) {
                        rv = *this;
                    } else {
                        rv = this->_engine->make_node(
                            other.key(), other.then_(), other.else_() | *this);
                    }
                }

                else if (other.is_one()) {
                    if (this->is_one() or this->is_zero()) {
                        rv = other;
                    } else {
                        rv = this->_engine->make_node(
                            this->key(), this->then_(), this->else_() | other);
                    }
                }

                else if (other.key() > this->key()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() | other);
                }

                else if (other.key() == this->key()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_() | other.then_(), this->else_() | other.else_());
                }

                else if (other.key() < this->key()) {
                    rv = this->_engine->make_node(
                        other.key(), other.then_(), other.else_() | *this);
                }

                cache_record.left = *this;
                cache_record.right = other;
                cache_record.result = rv;
                return rv;
            }

            Root operator& (const Root& other) const {
                if (this->is_zero()) {
                    return *this;
                } else if (other.is_zero()) {
                    return other;
                }

                // Try to get the result from the cache.
                auto& cache_record = this->_engine->_union_cache(*this, other);
                if ((cache_record.left == *this) and (cache_record.right == other)) {
                    return cache_record.result;
                }

                // Compute the result.
                Root rv;

                if (this->is_one()) {
                    const Root* else_most = &other;
                    while (!(else_most->is_zero() or else_most->is_one())) {
                        else_most = &else_most->else_();
                    }
                    rv = *else_most;
                }

                else if (other.is_one()) {
                    const Root* else_most = this;
                    while (!(else_most->is_zero() or else_most->is_one())) {
                        else_most = &else_most->else_();
                    }
                    rv = *else_most;
                }

                else if (other.key() > this->key()) {
                    rv = this->else_() & other;
                }

                else if (other.key() == this->key()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_() & other.then_(), this->else_() & other.else_());
                }

                else if (other.key() < this->key()) {
                    rv = *this & other.else_();
                }

                cache_record.left = *this;
                cache_record.right = other;
                cache_record.result = rv;
                return rv;
            }

            Root operator- (const Root& other) const {
                if (this->is_zero() or other.is_zero()) {
                    return *this;
                }

                // Try to get the result from the cache.
                auto& cache_record = this->_engine->_union_cache(*this, other);
                if ((cache_record.left == *this) and (cache_record.right == other)) {
                    return cache_record.result;
                }

                // Compute the result.
                Root rv;

                if (this->is_one()) {
                    const Root* else_most = &other;
                    while (!(else_most->is_zero() or else_most->is_one())) {
                        else_most = &else_most->else_();
                    }

                    if (else_most->is_zero()) {
                        rv = *this;
                    } else {
                        rv = this->_engine->make_terminal(false);
                    }
                }

                else if (other.is_one()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() - other);
                }

                else if (other.key() > this->key()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() - other);
                }

                else if (other.key() == this->key()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_() - other.then_(), this->else_() - other.else_());
                }

                else if (other.key() < this->key()) {
                    rv = *this - other.else_();
                }

                cache_record.left = *this;
                cache_record.right = other;
                cache_record.result = rv;
                return rv;
            }

            Root operator^ (const Root& other) const {
                if (this->is_zero()) {
                    return other;
                } else if (other.is_zero()) {
                    return *this;
                }

                // Try to get the result from the cache.
                auto& cache_record = this->_engine->_union_cache(*this, other);
                if ((cache_record.left == *this) and (cache_record.right == other)) {
                    return cache_record.result;
                }

                // Compute the result.
                Root rv;

                if (this->is_one()) {
                    if (other.is_one()) {
                        rv = this->_engine->make_terminal(false);
                    } else {
                        rv = this->_engine->make_node(
                            other.key(), other.then_(), *this ^ other.else_());
                    }
                }

                else if (other.is_one()) {
                    if (this->is_one()) {
                        rv = this->_engine->make_terminal(false);
                    } else {
                        rv = this->_engine->make_node(
                            this->key(), this->then_(), this->else_() ^ other);
                    }
                }

                else if (other.key() > this->key()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() ^ other);
                }

                else if (other.key() == this->key()) {
                    rv = this->_engine->make_node(
                        this->key(), this->then_() ^ other.then_(), this->else_() ^ other.else_());
                }

                else if (other.key() < this->key()) {
                    rv = this->_engine->make_node(
                        other.key(), other.then_(), *this ^ other.else_());
                }

                cache_record.left = *this;
                cache_record.right = other;
                cache_record.result = rv;
                return rv;
            }

            inline const Key& key() const {
                return this->node->key;
            }

            inline const Root& then_() const {
                return this->node->then_;
            }

            inline const Root& else_() const {
                return this->node->else_;
            }

            inline bool is_zero() const {
                return this->node == nullptr;
            }

            inline bool is_one() const {
                return (this->node != nullptr) and (this->node->terminal == true);
            }

            std::size_t size() const {
                if (this->is_zero()) {
                    return 0;
                } else {
                    return this->node->size;
                }
            }

            std::size_t hash() const {
                std::hash<const Node*> node_hasher;
                return node_hasher(this->node);
            }

            // Key key;
            const Node* node;
        };

        Engine(
            std::size_t union_cache_size=512,
            std::size_t intersection_cache_size=512,
            std::size_t difference_cache_size=512,
            std::size_t symmetric_difference_cache_size=512
        ) :
            _unique_table(),
            _union_cache(union_cache_size),
            _intersection_cache(intersection_cache_size),
            _difference_cache(difference_cache_size),
            _symmetric_difference_cache(symmetric_difference_cache_size)
        {
            // fixme: Throw an exception if the user tries to set a cache size
            // lower than 1.
            this->_unique_table._engine = this;
        }

        Engine(const Engine&) = delete;
        Engine(Engine&&) = delete;
        Engine& operator= (const Engine&) = delete;
        Engine& operator= (Engine&&) = delete;

        Root make_node(Key key, const Root& then_, const Root& else_) {
            if (then_.is_zero()) {
                return else_;
            }

            return this->_unique_table[Node(key, then_, else_)];
        }

        Root make_terminal(bool terminal) {
            if (terminal) {
                return this->_unique_table[Node(true)];
            } else {
                return Root();
            }
        }

    private:
        friend class Root;

        struct NodeHasher {
            std::size_t operator() (const Node& node) const {
                return node.hash();
            }
        };

        class Node {
        public:
            Node()
            : ref_count(0), size(0), terminal(false), key() {
            }

            Node(const Key& key, const Root& then_, const Root& else_)
            : ref_count(0), size(then_.size() + else_.size()), terminal(false),
              key(key), then_(then_), else_(else_) {
            }

            Node(bool terminal)
            : ref_count(0), size(terminal ? 1 : 0), terminal(terminal), key() {
            }

            bool operator== (const Node& other) const {
                return
                    (this->terminal == other.terminal)
                    and (this->key == other.key)
                    and (this->then_ == other.then_)
                    and (this->else_ == other.else_);
            }

            std::size_t hash() const {
                std::hash<bool> bool_hasher;
                std::hash<Key> key_hasher;

                std::size_t rv = 0;
                boost::hash_combine(rv, bool_hasher(this->terminal));
                boost::hash_combine(rv, key_hasher(this->key));
                boost::hash_combine(rv, this->then_.hash());
                boost::hash_combine(rv, this->else_.hash());

                return rv;
            }

            mutable std::size_t ref_count;
            mutable std::size_t size;

            bool terminal;
            Key key;
            Root then_;
            Root else_;
            // Key then_key;
            // Key else_key;
        };

        class UniqueTable {
        public:
            void destroy_node(const Node* node) {
                this->_nodes.erase(*node);
            }

            Root operator[] (const Node& node) {
                // Look for a node that matches the input in the table.
                auto it = this->_nodes.find(node);
                if (it != this->_nodes.end()) {
                    return Root(*this->_engine, &(*it));
                }

                // Insert the new node in the table.
                auto res = this->_nodes.insert(node);
                return Root(*this->_engine, &(*res.first));
            }

            Engine* _engine;

        private:
            std::unordered_set<Node, NodeHasher> _nodes;
        };

        class Cache {
        public:
            struct CacheRecord {
                CacheRecord() {}

                Root left;
                Root right;
                Root result;
            };

            Cache(const std::size_t size)
            : _store(new CacheRecord[size]), _store_size(size) {
            }

            ~Cache() {
                delete[] this->_store;
            }

            CacheRecord& operator() (const Root& left, const Root& right) {
                std::size_t h = left.hash();
                boost::hash_combine(h, right.hash());
                return this->_store[h % this->_store_size];
            }

        private:
            CacheRecord* _store;
            const std::size_t _store_size;
        };

        UniqueTable _unique_table;
        Cache _union_cache;
        Cache _intersection_cache;
        Cache _difference_cache;
        Cache _symmetric_difference_cache;
    };

}

#endif
