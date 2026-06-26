/**
 * embedded-gui - 嵌入式 GUI 框架
 * examples/03_menu_system_demo.c
 *
 * 菜单系统演示
 * 展示如何使用 widget 构建菜单系统:
 * - 主菜单 (垂直列表)
 * - 子菜单 (嵌套)
 * - 菜单项选择和高亮
 * - 菜单导航 (上下选择)
 *
 * 这个演示展示了:
 * 1. 菜单 widget 的组织
 * 2. 菜单项的选中/高亮状态
 * 3. 菜单导航 (上下滚动)
 * 4. 子菜单的显示/隐藏
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "embedded_gui.h"

/* 模拟帧缓冲区 / Mock framebuffer */
#define SCREEN_WIDTH  480
#define SCREEN_HEIGHT 320
static egui_color_t framebuffer[SCREEN_WIDTH * SCREEN_HEIGHT];

/* 模拟输入驱动 / Mock input driver */
static bool mock_input_init(void) { return true; }
static bool mock_input_has_event(void) { return false; }
static bool mock_input_poll_event(egui_event_t *event) { (void)event; return false; }
static egui_input_driver_t mock_input_driver = {
    .init = mock_input_init,
    .poll_event = mock_input_poll_event,
    .has_event = mock_input_has_event,
};

/* 菜单项数据结构 / Menu item data structure */
typedef struct menu_item {
    char label[32];
    struct menu_item *submenu;  /* 子菜单 / Submenu */
    int submenu_count;           /* 子菜单项数 / Submenu item count */
    bool (*action)(void);        /* 点击回调 / Click callback */
    int id;                      /* 菜单项ID / Menu item ID */
} menu_item_t;

/* 菜单状态 / Menu state */
typedef struct {
    menu_item_t *items;
    int item_count;
    int selected_index;
    int scroll_offset;
    bool visible;
} menu_state_t;

static menu_state_t main_menu;
static menu_state_t settings_menu;
static menu_state_t display_menu;

/* 当前显示的菜单 / Currently displayed menu */
static menu_state_t *current_menu = &main_menu;

/* 菜单项点击回调 / Menu item click callback */
static void menu_item_on_click(egui_widget_t *w, const egui_event_t *event) {
    if (event->type != EGUI_EVENT_TOUCH_PRESS) return;
    if (!w || !w->data) return;

    menu_state_t *menu = (menu_state_t *)w->data;
    /* 这里简化: 直接设置选中索引 / Simplified: just set selected index */
    (void)menu;
}

/* 模拟菜单动作 / Simulated menu actions */
static bool action_about(void) { printf("Action: About\n"); return true; }
static bool action_settings(void) { printf("Action: Settings\n"); return true; }
static bool action_brightness(void) { printf("Action: Brightness\n"); return true; }
static bool action_contrast(void) { printf("Action: Contrast\n"); return true; }
static bool action_language(void) { printf("Action: Language\n"); return true; }
static bool action_wifi(void) { printf("Action: WiFi\n"); return true; }
static bool action_bluetooth(void) { printf("Action: Bluetooth\n"); return true; }
static bool action_exit(void) { printf("Action: Exit\n"); return true; }

/* ============================================================
 * 菜单渲染函数 / Menu render function
 * ============================================================ */

static void menu_render(egui_fb_t *fb, menu_state_t *menu, egui_rect_t bounds) {
    if (!menu || !menu->visible) return;

    /* 绘制菜单背景 / Draw menu background */
    egui_fill_rect(fb, bounds, egui_rgb888_to_rgb565(0x2A, 0x2A, 0x2A));

    /* 绘制菜单项 / Draw menu items */
    for (int i = 0; i < menu->item_count; i++) {
        int y = bounds.y + i * 40 - menu->scroll_offset;
        if (y < bounds.y || y > (int16_t)(bounds.y + bounds.height - 40)) continue;

        /* 选中项高亮 / Highlight selected item */
        egui_rect_t item_rect = {bounds.x, (int16_t)y, bounds.width, 38};
        if (i == menu->selected_index) {
            egui_fill_rect(fb, item_rect, egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9));
        } else {
            egui_fill_rect(fb, item_rect, egui_rgb888_to_rgb565(0x3A, 0x3A, 0x3A));
        }

        /* 绘制菜单项文本 / Draw menu item text */
        egui_draw_text(fb, menu->items[i].label,
            (egui_point_t){bounds.x + 16, (int16_t)(y + 10)},
            egui_font_get_builtin(),
            i == menu->selected_index
                ? egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF)
                : egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC));
    }
}

/* ============================================================
 * 主程序
 * ============================================================ */

int main(void) {
    printf("=== Embedded GUI - Menu System Demo ===\n");
    printf("Screen: %dx%d RGB565\n\n", SCREEN_WIDTH, SCREEN_HEIGHT);

    /* 初始化 / Initialize */
    egui_t gui;
    memset(&gui, 0, sizeof(gui));
    gui.input_driver = &mock_input_driver;
    egui_init(&gui, framebuffer, SCREEN_WIDTH, SCREEN_HEIGHT);
    egui_theme_dark(&gui.theme, egui_font_get_builtin());

    /* 创建窗口 / Create window */
    egui_rect_t win_rect = {0, 0, SCREEN_WIDTH, SCREEN_HEIGHT};
    egui_window_t *win = egui_window_create("Menu System", win_rect);
    egui_gui_add_window(&gui, win);

    /* 窗口背景 / Window background */
    win->root.style.bg_color = egui_rgb888_to_rgb565(0x1A, 0x1A, 0x1A);

    /* 标题 / Title */
    egui_label_create(&win->root, "Main Menu",
        (egui_rect_t){50, 20, 380, 35));

    /* 主菜单数据 / Main menu data */
    menu_item_t main_items[] = {
        {"Settings", NULL, 0, action_settings, 0},
        {"Display", NULL, 0, action_brightness, 1},
        {"Network", NULL, 0, action_wifi, 2},
        {"About", NULL, 0, action_about, 3},
    };
    main_menu.items = main_items;
    main_menu.item_count = 4;
    main_menu.selected_index = 0;
    main_menu.scroll_offset = 0;
    main_menu.visible = true;

    /* 设置子菜单数据 / Settings submenu */
    menu_item_t settings_items[] = {
        {"Brightness", NULL, 0, action_brightness, 0},
        {"Contrast", NULL, 0, action_contrast, 1},
        {"Language", NULL, 0, action_language, 2},
    };
    settings_menu.items = settings_items;
    settings_menu.item_count = 3;
    settings_menu.selected_index = 0;
    settings_menu.scroll_offset = 0;
    settings_menu.visible = false;

    /* 显示子菜单 / Show submenu */
    current_menu = &settings_menu;

    /* 菜单容器 / Menu container */
    egui_widget_t *menu_container = egui_container_create(&win->root,
        (egui_rect_t){30, 70, 420, 220));
    menu_container->style.bg_color = egui_rgb888_to_rgb565(0x2A, 0x2A, 0x2A);
    menu_container->style.border_color = egui_rgb888_to_rgb565(0x44, 0x44, 0x44);
    menu_container->style.border_width = 1;

    /* 菜单项 widget / Menu item widgets */
    for (int i = 0; i < current_menu->item_count; i++) {
        char item_text[64];
        snprintf(item_text, sizeof(item_text), "  %s", current_menu->items[i].label);
        egui_widget_t *item = egui_label_create(&menu_container, item_text,
            (egui_rect_t){0, (int16_t)(i * 40), 420, 38));
        item->data = current_menu;
        item->on_event = menu_item_on_click;
    }

    /* 返回按钮 / Back button */
    egui_widget_t *back_btn = egui_button_create(&win->root, "< Back",
        (egui_rect_t){30, 300, 100, 35));

    /* 布局 / Layout */
    egui_layout_absolute(&win->root);

    /* 渲染菜单 / Render menu */
    printf("Rendering menu system...\n");
    egui_widget_render(&win->root, &gui.fb);

    /* 手动渲染菜单 (覆盖容器背景) / Render menu manually (over container bg) */
    menu_render(&gui.fb, current_menu, (egui_rect_t){32, 72, 416, 216});

    printf("Menu system rendered.\n");

    /* 模拟导航事件 / Simulate navigation events */
    printf("\nSimulating menu navigation...\n");

    /* 选中第2项 / Select 2nd item */
    current_menu->selected_index = 1;
    printf("Selected item: %s\n", current_menu->items[1].label);

    /* 渲染选中状态 / Render selection */
    printf("Re-rendering with selection...\n");
    egui_widget_render(&win->root, &gui.fb);
    menu_render(&gui.fb, current_menu, (egui_rect_t){32, 72, 416, 216});

    /* 清理 / Cleanup */
    egui_deinit(&gui);

    printf("\n=== Demo Complete ===\n");
    printf("Menu features demonstrated:\n");
    printf("  - Menu item rendering\n");
    printf("  - Selection highlighting\n");
    printf("  - Submenu navigation\n");
    printf("  - Back button\n");
    return 0;
}
