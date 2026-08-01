#include <iostream>

namespace resonith::internal {

bool partial_graph_generation_arena_probe() noexcept;

}  // namespace resonith::internal

int main() {
    if (!resonith::internal::partial_graph_generation_arena_probe()) {
        std::cerr << "R203_TYPED_REJECTION:state-arena-transaction\n";
        return 1;
    }
    std::cout
        << "{\"schema\":\"resonith-r203-state-arena-hostile-1\","
        << "\"status\":\"passed\"}\n";
    return 0;
}
