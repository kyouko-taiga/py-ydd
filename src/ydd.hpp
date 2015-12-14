#ifndef __cppydd_ydd__
#define __cppydd_ydd__

#include <cstddef>
#include <functional>
#include <stdexcept>


namespace ydd {

    template <typename Config>
    class Engine {
    private:
        using Key = typename Config::Key;

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
                        this->node->~Node();
                        this->node = nullptr;
                    }
                }
            }

            Root& operator= (const Root& other) {
                if (this->node != nullptr) {
                    this->node->ref_count--;
                    if (this->node->ref_count == 0) {
                        this->node->~Node();
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
                } else {
                    cache_record.left = *this;
                    cache_record.right = other;
                }

                if (this->is_one()) {
                    if (other.is_one() or other.is_zero()) {
                        cache_record.result = *this;
                    } else {
                        cache_record.result = this->_engine->make_node(
                            other.key(), other.then_(), other.else_() | *this);
                    }
                }

                else if (other.is_one()) {
                    if (this->is_one() or this->is_zero()) {
                        cache_record.result = other;
                    } else {
                        cache_record.result = this->_engine->make_node(
                            this->key(), this->then_(), this->else_() | other);
                    }
                }

                else if (other.key() > this->key()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() | other);
                }

                else if (other.key() == this->key()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_() | other.then_(), this->else_() | other.else_());
                }

                else if (other.key() < this->key()) {
                    cache_record.result = this->_engine->make_node(
                        other.key(), other.then_(), other.else_() | *this);
                }

                return cache_record.result;
            }

            Root operator& (const Root& other) const {
                if (this->is_zero()) {
                    return *this;
                } else if (other.is_zero()) {
                    return other;
                }

                // Try to get the result from the cache.
                auto& cache_record = this->_engine->_intersection_cache(*this, other);
                if ((cache_record.left == *this) and (cache_record.right == other)) {
                    return cache_record.result;
                } else {
                    cache_record.left = *this;
                    cache_record.right = other;
                }

                if (this->is_one()) {
                    const Root* else_most = &other;
                    while (!(else_most->is_zero() or else_most->is_one())) {
                        else_most = &else_most->else_();
                    }
                    cache_record.result = *else_most;
                }

                else if (other.is_one()) {
                    const Root* else_most = this;
                    while (!(else_most->is_zero() or else_most->is_one())) {
                        else_most = &else_most->else_();
                    }
                    cache_record.result = *else_most;
                }

                else if (other.key() > this->key()) {
                    cache_record.result = this->else_() & other;
                }

                else if (other.key() == this->key()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_() & other.then_(), this->else_() & other.else_());
                }

                else if (other.key() < this->key()) {
                    cache_record.result = *this & other.else_();
                }

                return cache_record.result;
            }

            Root operator- (const Root& other) const {
                if (this->is_zero() or other.is_zero()) {
                    return *this;
                }

                // Try to get the result from the cache.
                auto& cache_record = this->_engine->_difference_cache(*this, other);
                if ((cache_record.left == *this) and (cache_record.right == other)) {
                    return cache_record.result;
                } else {
                    cache_record.left = *this;
                    cache_record.right = other;
                }

                if (this->is_one()) {
                    const Root* else_most = &other;
                    while (!(else_most->is_zero() or else_most->is_one())) {
                        else_most = &else_most->else_();
                    }

                    if (else_most->is_zero()) {
                        cache_record.result = *this;
                    } else {
                        cache_record.result = this->_engine->make_terminal(false);
                    }
                }

                else if (other.is_one()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() - other);
                }

                else if (other.key() > this->key()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() - other);
                }

                else if (other.key() == this->key()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_() - other.then_(), this->else_() - other.else_());
                }

                else if (other.key() < this->key()) {
                    cache_record.result = *this - other.else_();
                }

                return cache_record.result;
            }

            Root operator^ (const Root& other) const {
                if (this->is_zero()) {
                    return other;
                } else if (other.is_zero()) {
                    return *this;
                }

                // Try to get the result from the cache.
                auto& cache_record = this->_engine->_symmetric_difference_cache(*this, other);
                if ((cache_record.left == *this) and (cache_record.right == other)) {
                    return cache_record.result;
                } else {
                    cache_record.left = *this;
                    cache_record.right = other;
                }

                if (this->is_one()) {
                    if (other.is_one()) {
                        cache_record.result = this->_engine->make_terminal(false);
                    } else {
                        cache_record.result = this->_engine->make_node(
                            other.key(), other.then_(), *this ^ other.else_());
                    }
                }

                else if (other.is_one()) {
                    if (this->is_one()) {
                        cache_record.result = this->_engine->make_terminal(false);
                    } else {
                        cache_record.result = this->_engine->make_node(
                            this->key(), this->then_(), this->else_() ^ other);
                    }
                }

                else if (other.key() > this->key()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_(), this->else_() ^ other);
                }

                else if (other.key() == this->key()) {
                    cache_record.result = this->_engine->make_node(
                        this->key(), this->then_() ^ other.then_(), this->else_() ^ other.else_());
                }

                else if (other.key() < this->key()) {
                    cache_record.result = this->_engine->make_node(
                        other.key(), other.then_(), *this ^ other.else_());
                }

                return cache_record.result;
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

        Engine()
        : _union_cache(Config::union_cache_size),
          _intersection_cache(Config::intersection_cache_size),
          _difference_cache(Config::difference_cache_size),
          _symmetric_difference_cache(Config::symmetric_difference_cache_size) {
            this->_unique_table._engine = this;
        }

        Engine(const Engine&) = delete;
        Engine(Engine&&) = delete;
        Engine& operator= (const Engine&) = delete;
        Engine& operator= (Engine&&) = delete;

        ~Engine() {}

        Root make_node(Key key, const Root& then_, const Root& else_) {
            if (then_.is_zero()) {
                return else_;
            }

            return this->_unique_table[Node(key, then_, else_)];
        }

        Root make_terminal(bool terminal) {
            if (terminal) {
                return this->_unique_table[Node(terminal)];
            } else {
                return Root();
            }
        }

    private:
        friend class Root;

        class Cache {
        public:
            struct CacheRecord {
                CacheRecord() {}
                CacheRecord(const Root* left, const Root* right, const Root* result)
                : left(left), right(right), result(result) {
                }

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
                h ^= right.hash() + 0x9e3779b9 + (h << 6) + (h >> 2);
                return this->_store[h % this->_store_size];
            }

        private:
            CacheRecord* _store;
            const std::size_t _store_size;
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
                    // and (this->then_key == other.then_key)
                    // and (this->else_key == other.else_key);
            }

            std::size_t hash() const {
                std::hash<bool> bool_hasher;
                // fixme (std::hash<Root>)
                std::hash<Key> key_hasher;
                
                std::size_t rv = 0;
                rv ^= bool_hasher(this->terminal) + 0x9e3779b9 + (rv << 6) + (rv >> 2);
                rv ^= this->then_.hash() + 0x9e3779b9 + (rv << 6) + (rv >> 2);
                rv ^= this->else_.hash() + 0x9e3779b9 + (rv << 6) + (rv >> 2);
                rv ^= key_hasher(this->key) + 0x9e3779b9 + (rv << 6) + (rv >> 2);
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
            UniqueTable()
            : nodes(new Node[Config::buckets_nb * Config::buckets_security]) {
            }

            ~UniqueTable() {
                delete[] this->nodes;
            }

            Root operator[] (const Node& node) {
                // Check whether the node already exists in the table.
                std::size_t idx = (node.hash() % Config::buckets_nb) * Config::buckets_security;
                for (auto i = idx; i < idx + Config::buckets_security; ++i) {
                    if ((this->nodes[i].ref_count > 0) and (node == this->nodes[i])) {
                        // To change when we'll be using attributed edges.
                        return Root(*this->_engine, &this->nodes[i]);
                    }
                }

                // Insert the new node in the table.
                for (auto i = idx; i < idx + Config::buckets_security; ++i) {
                    if (this->nodes[i].ref_count == 0) {
                        this->nodes[i] = std::move(node);
                        
                        // To change when we'll be using attributed edges.
                        return Root(*this->_engine, &this->nodes[i]);
                    }
                }

                throw std::overflow_error("The table is full.");
            }

            Engine* _engine;
            Node* nodes;
        };

        UniqueTable _unique_table;
        Cache _union_cache;
        Cache _intersection_cache;
        Cache _difference_cache;
        Cache _symmetric_difference_cache;
    };

}

#endif
