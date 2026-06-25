/**
 * @file mixin.cpp
 * @brief Mixin 模式示例
 *
 * 通过模板组合多个功能模块，实现灵活的功能组合。
 */

#include <iostream>
#include <string>
#include "../include/advanced_templates/mixin.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Mixin Pattern Demo ===" << std::endl;
    std::cout << std::endl;

    // 1. 游戏实体系统
    std::cout << "--- 1. Game Entity System ---" << std::endl;
    GameEntity player;
    player.name = "Player";
    player.id = 1;
    player.set_position(100.0f, 200.0f);
    player.set_sprite("hero.png");
    player.set_health(100);

    std::cout << "Entity: " << player.name << std::endl;
    std::cout << "Position: (" << player.get_x() << ", " << player.get_y() << ")" << std::endl;
    std::cout << "Health: " << player.get_health() << std::endl;
    std::cout << "Alive: " << (player.is_alive() ? "yes" : "no") << std::endl;

    player.move(10.0f, -5.0f);
    std::cout << "After move: (" << player.get_x() << ", " << player.get_y() << ")" << std::endl;

    player.take_damage(30);
    std::cout << "After damage: " << player.get_health() << " HP" << std::endl;

    player.render();
    std::cout << std::endl;

    // 2. Mixin 组合说明
    std::cout << "--- 2. Mixin Composition ---" << std::endl;
    std::cout << "GameEntity = BaseEntity + Movable + Renderable + HasHealth" << std::endl;
    std::cout << std::endl;
    std::cout << "Available mixins:" << std::endl;
    std::cout << "  - Loggable: Adds logging functionality" << std::endl;
    std::cout << "  - Observable: Adds observer pattern" << std::endl;
    std::cout << "  - Validatable: Adds validation" << std::endl;
    std::cout << "  - Cacheable: Adds caching" << std::endl;
    std::cout << "  - TimerMixin: Adds timing" << std::endl;
    std::cout << std::endl;

    // 3. Mixin 组合器
    std::cout << "--- 3. Mixin Combiner ---" << std::endl;
    std::cout << "Usage: using MyType = mixin_t<Base, Mixin1, Mixin2, Mixin3>;" << std::endl;
    std::cout << "This creates: Mixin3<Mixin2<Mixin1<Base>>>" << std::endl;
    std::cout << std::endl;

    // 4. 可观察对象
    std::cout << "--- 4. Observable Pattern ---" << std::endl;
    std::cout << "Observable mixin allows subscribing to events:" << std::endl;
    std::cout << "  obj.subscribe([](const Event& e) { ... });" << std::endl;
    std::cout << "  obj.notify(event);" << std::endl;

    return 0;
}
