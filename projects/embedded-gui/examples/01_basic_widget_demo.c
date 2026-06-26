/**
 * embedded-gui - 嵌入式 GUI 框架
 * examples/01_basic_widget_demo.c
 *
 * 基础 Widget 演示
 * 展示所有基本 widget 类型:
 * - 按钮 (Button)
 * - 标签 (Label)
 * - 文本框 (Textbox)
 * - 滑块 (Slider)
 * - 复选框 (Checkbox)
 *
 * 这个演示展示了:
 * 1. Widget 的创建和布局
 * 2. 事件回调的设置
 * 3. Widget 状态的改变
 * 4. 渲染流程
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "embedded_gui.h"

/* 模拟帧缓冲区 (800x480 RGB565) */
#define SCREEN_WIDTH  800
#define SCREEN_HEIGHT 480
static egui_color_t framebuffer[SCREEN_WIDTH * SCREEN_HEIGHT];

/* 模拟触摸输入数据结构 */
typedef struct {
    int x;
    int y;
    int button; /* 0=release, 1=press */
} mock_touch_t;

/* 模拟触摸事件队列 */
#define TOUCH_QUEUE_SIZE 256
static mock_touch_t touch_queue[TOUCH_QUEUE_SIZE];
static int touch_head = 0;
static int touch_tail = 0;

/* 推送模拟触摸事件 */
static void push_touch(int x, int y, int button) {
    int next = (touch_tail + 1) % TOUCH_QUEUE_SIZE;
    if (next != touch_head) {
        touch_queue[touch_tail].x = x;
        touch_queue[touch_tail].y = y;
        touch_queue[touch_tail].button = button;
        touch_tail = next;
    }
}

/* 模拟输入驱动 */
static bool mock_input_init(void) { return true; }
static bool mock_input_has_event(void) { return touch_head != touch_tail; }
static bool mock_input_poll_event(egui_event_t *event) {
    if (touch_head == touch_tail) return false;
    event->type = EGUI_EVENT_TOUCH_PRESS;
    event->pos.x = touch_queue[touch_head].x;
    event->pos.y = touch_queue[touch_head].y;
    event->key_code = 0;
    event->timestamp = 0;
    event->user_data = NULL;
    touch_head = (touch_head + 1) % TOUCH_QUEUE_SIZE;
    return true;
}
static egui_input_driver_t mock_input_driver = {
    .init = mock_input_init,
    .poll_event = mock_input_poll_event,
    .has_event = mock_input_has_event,
};

/* ============================================================
 * 按钮点击回调
 * ============================================================ */

static void button_on_click(egui_widget_t *w, const egui_event_t *event) {
    if (event->type == EGUI_EVENT_TOUCH_PRESS) {
        /* 按钮按下: 切换状态 / Toggle state on press */
        if (w->data) {
            egui_button_data_t *data = (egui_button_data_t *)w->data;
            if (strcmp(data->text, "Clicked!") == 0) {
                strncpy(data->text, "Button", sizeof(data->text) - 1);
            } else {
                strncpy(data->text, "Clicked!", sizeof(data->text) - 1);
            }
        }
    }
}

/* ============================================================
 * 复选框回调
 * ============================================================ */

static void checkbox_on_toggle(egui_widget_t *w, const egui_event_t *event) {
    if (event->type == EGUI_EVENT_TOUCH_PRESS && w->data) {
        egui_checkbox_data_t *data = (egui_checkbox_data_t *)w->data;
        data->checked = !data->checked;
        printf("Checkbox toggled: %s\n", data->checked ? "ON" : "OFF");
    }
}

/* ============================================================
 * 主程序
 * ============================================================ */

int main(void) {
    printf("=== Embedded GUI - Basic Widget Demo ===\n");
    printf("Screen: %dx%d RGB565\n", SCREEN_WIDTH, SCREEN_HEIGHT);
    printf("\n");

    /* 1. 初始化 GUI / Initialize GUI */
    egui_t gui;
    memset(&gui, 0, sizeof(gui));
    gui.display_driver = NULL; /* 无硬件驱动 / No hardware driver */
    gui.input_driver = &mock_input_driver;

    egui_init(&gui, framebuffer, SCREEN_WIDTH, SCREEN_HEIGHT);
    egui_theme_default(&gui.theme, egui_font_get_builtin());

    /* 2. 创建窗口 / Create window */
    egui_rect_t win_rect = {0, 0, SCREEN_WIDTH, SCREEN_HEIGHT};
    egui_window_t *win = egui_window_create("Basic Widget Demo", win_rect);
    egui_gui_add_window(&gui, win);

    /* 设置窗口根组件样式 / Set window root style */
    win->root.style.bg_color = egui_rgb888_to_rgb565(0xF5, 0xF5, 0xF5);
    win->root.style.border_width = 0;

    /* 3. 创建标题标签 / Create title label */
    egui_label_create(&win->root, "Embedded GUI Demo",
        (egui_rect_t){50, 30, 700, 40});

    /* 4. 创建按钮 / Create buttons */
    egui_widget_t *btn1 = egui_button_create(&win->root, "Click Me!",
        (egui_rect_t){50, 100, 150, 50});
    btn1->on_event = button_on_click;

    egui_widget_t *btn2 = egui_button_create(&win->root, "Reset",
        (egui_rect_t){220, 100, 100, 50});
    btn2->on_event = button_on_click;

    /* 5. 创建状态标签 / Create status label */
    egui_widget_t *status_label = egui_label_create(&win->root, "Status: Ready",
        (egui_rect_t){50, 170, 300, 30});

    /* 6. 创建文本框 / Create textbox */
    char text_buf[64] = "Hello, GUI!";
    egui_widget_t *textbox = egui_textbox_create(&win->root, text_buf, sizeof(text_buf),
        (egui_rect_t){50, 220, 300, 40});

    /* 7. 创建滑块 / Create slider */
    egui_widget_t *slider = egui_slider_create(&win->root, 0, 100, 50,
        (egui_rect_t){50, 280, 300, 30});

    /* 8. 创建滑块值标签 / Create slider value label */
    egui_widget_t *slider_label = egui_label_create(&win->root, "Value: 50",
        (egui_rect_t){50, 320, 100, 25});

    /* 9. 创建复选框 / Create checkbox */
    egui_widget_t *checkbox = egui_checkbox_create(&win->root, "Enable Feature", true,
        (egui_rect_t){50, 360, 200, 30});
    checkbox->on_event = checkbox_on_toggle;

    /* 10. 创建容器 / Create container */
    egui_widget_t *container = egui_container_create(&win->root,
        (egui_rect_t){400, 80, 350, 350});

    /* 在容器中创建子组件 / Create children in container */
    egui_widget_t *info_label = egui_label_create(container,
        "Widget Demo\n\nThis demo shows all basic widget types:\n"
        "- Button (clickable)\n"
        "- Label (text display)\n"
        "- Textbox (text input)\n"
        "- Slider (value selection)\n"
        "- Checkbox (toggle)\n\n"
        "All rendered to framebuffer!",
        (egui_rect_t){10, 10, 330, 330});

    /* 11. 布局计算 / Layout calculation */
    egui_layout_absolute(&win->root);

    /* 12. 手动渲染一帧 (演示) / Render one frame manually (demo) */
    printf("Rendering frame...\n");
    egui_widget_render(&win->root, &gui.fb);
    printf("Frame rendered to framebuffer (%d pixels)\n", SCREEN_WIDTH * SCREEN_HEIGHT);

    /* 13. 模拟一些触摸事件 / Simulate some touch events */
    printf("\nSimulating touch events...\n");

    /* 点击按钮 / Click button */
    egui_event_t event;
    memset(&event, 0, sizeof(event));
    event.type = EGUI_EVENT_TOUCH_PRESS;
    event.pos.x = 100; /* 在 btn1 区域内 / Inside btn1 area */
    event.pos.y = 120;
    event.timestamp = 0;

    egui_event_dispatch(&gui, &event);
    printf("Event: Touch at (%d, %d)\n", event.pos.x, event.pos.y);

    /* 点击复选框 / Click checkbox */
    event.pos.x = 100;
    event.pos.y = 370;
    egui_event_dispatch(&gui, &event);
    printf("Event: Touch at (%d, %d)\n", event.pos.x, event.pos.y);

    /* 14. 再次渲染 (状态已改变) / Render again (state has changed) */
    printf("\nRe-rendering after events...\n");
    egui_widget_render(&win->root, &gui.fb);
    printf("Frame re-rendered.\n");

    /* 15. 清理 / Cleanup */
    egui_deinit(&gui);

    printf("\n=== Demo Complete ===\n");
    printf("In a real embedded system, the framebuffer would be:\n");
    printf("  1. Sent to LCD via SPI/RGB interface\n");
    printf("  2. Touch events would come from touchscreen driver\n");
    printf("  3. The event loop would run continuously\n");

    return 0;
}
