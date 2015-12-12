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

            Root operator+ (const Root& other) const {
                if (this->is_zero()) {
                    return other;
                }

                if (other.is_zero()) {
                    return *this;
                }

                if (this->is_one()) {
                    if (other.is_one() or other.is_zero()) {
                        return *this;
                    } else {
                        return this->_engine->make_node(
                            other.key(), other.then_(), other.else_() + *this);
                    }
                }

                if (other.is_one()) {
                    if (this->is_one() or this->is_zero()) {
                        return other;
                    } else {
                        return this->_engine->make_node(
                            this->key(), this->then_(), this->else_() + other);
                    }
                }

                if (other.key() > this->key()) {
                    return this->_engine->make_node(
                        this->key(), this->then_(), this->else_() + other);
                }

                if (other.key() == this->key()) {
                    return this->_engine->make_node(
                        this->key(), this->then_() + other.then_(), this->else_() + other.else_());
                }

                if (other.key() < this->key()) {
                    return this->_engine->make_node(
                        other.key(), other.then_(), other.else_() + *this);
                }

                return *this;
            }

            // Key key;
            const Node* node;

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

            std::size_t hash() const {
                std::hash<const Node*> node_hasher;
                return node_hasher(this->node);
            }

            bool operator== (const Root& other) const {
                return this->node == other.node;
            }
        };

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
            : key(), ref_count(0), terminal(false) {
            }

            Node(const Key& key, const Root& then_, const Root& else_)
            : key(key), then_(then_), else_(else_), ref_count(0), terminal(false) {
            }

            Node(bool terminal)
            : ref_count(0), terminal(terminal) {
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

            bool operator== (const Node& other) const {
                return
                    (this->terminal == other.terminal)
                    and (this->key == other.key)
                    and (this->then_ == other.then_)
                    and (this->else_ == other.else_);
                    // and (this->then_key == other.then_key)
                    // and (this->else_key == other.else_key);
            }

            bool terminal;
            Root then_;
            Root else_;
            Key key;
            // Key then_key;
            // Key else_key;

            mutable std::size_t ref_count;
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
        Cache _cache;

    public:
        Engine() {
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

    };

}
