/**
 * embedded-gui - 嵌入式 GUI 框架
 * examples/02_form_interface_demo.c
 *
 * 表单界面演示
 * 展示如何使用 widget 构建表单界面:
 * - 输入字段 (用户名、密码等)
 * - 提交/取消按钮
 * - 验证反馈
 * - 布局管理
 *
 * 这个演示展示了:
 * 1. 表单界面的 widget 组织
 * 2. 文本框的交互
 * 3. 按钮的事件处理
 * 4. 状态反馈 (成功/错误提示)
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

/* 表单数据 / Form data */
typedef struct {
    char username[32];
    char password[32];
    char email[64];
    bool remember_me;
    bool terms_accepted;
    int notification_pref; /* 0=none, 1=email, 2=push */
} form_data_t;

static form_data_t form_data;
static char form_status[128] = "";

/* ============================================================
 * 按钮回调 / Button callbacks
 * ============================================================ */

static void submit_on_click(egui_widget_t *w, const egui_event_t *event) {
    (void)w;
    if (event->type != EGUI_EVENT_TOUCH_PRESS) return;

    /* 验证表单 / Validate form */
    if (strlen(form_data.username) == 0) {
        strncpy(form_status, "Error: Username required", sizeof(form_status) - 1);
        return;
    }
    if (strlen(form_data.password) == 0) {
        strncpy(form_status, "Error: Password required", sizeof(form_status) - 1);
        return;
    }

    /* 模拟提交 / Simulate submission */
    printf("\n=== Form Submitted ===\n");
    printf("Username: %s\n", form_data.username);
    printf("Password: %s\n", form_data.password);
    printf("Email:    %s\n", form_data.email);
    printf("Remember: %s\n", form_data.remember_me ? "Yes" : "No");
    printf("Terms:    %s\n", form_data.terms_accepted ? "Accepted" : "Not accepted");
    printf("Notify:   %s\n", form_data.notification_pref == 0 ? "None" :
                                    form_data.notification_pref == 1 ? "Email" : "Push");
    printf("======================\n\n");

    strncpy(form_status, "Submitted successfully!", sizeof(form_status) - 1);
}

static void cancel_on_click(egui_widget_t *w, const egui_event_t *event) {
    (void)w;
    if (event->type != EGUI_EVENT_TOUCH_PRESS) return;

    /* 清空表单 / Clear form */
    memset(&form_data, 0, sizeof(form_data));
    form_data.notification_pref = 0;
    strncpy(form_status, "Form cleared", sizeof(form_status) - 1);
}

/* 复选框回调 / Checkbox callbacks */
static void remember_on_toggle(egui_widget_t *w, const egui_event_t *event) {
    if (event->type == EGUI_EVENT_TOUCH_PRESS && w->data) {
        /* 复选框数据存储在 widget data 中，使用通用指针访问 / Checkbox data stored in widget data */
        int *checked = (int *)w->data;
        form_data.remember_me = (*checked != 0);
        (void)w;
    }
}

static void terms_on_toggle(egui_widget_t *w, const egui_event_t *event) {
    if (event->type == EGUI_EVENT_TOUCH_PRESS && w->data) {
        int *checked = (int *)w->data;
        form_data.terms_accepted = (*checked != 0);
        (void)w;
    }
}

/* ============================================================
 * 主程序
 * ============================================================ */

int main(void) {
    printf("=== Embedded GUI - Form Interface Demo ===\n");
    printf("Screen: %dx%d RGB565\n\n", SCREEN_WIDTH, SCREEN_HEIGHT);

    /* 初始化 / Initialize */
    egui_t gui;
    memset(&gui, 0, sizeof(gui));
    gui.input_driver = &mock_input_driver;
    egui_init(&gui, framebuffer, SCREEN_WIDTH, SCREEN_HEIGHT);
    egui_theme_dark(&gui.theme, egui_font_get_builtin());

    /* 创建窗口 / Create window */
    egui_rect_t win_rect = {0, 0, SCREEN_WIDTH, SCREEN_HEIGHT};
    egui_window_t *win = egui_window_create("Login Form", win_rect);
    egui_gui_add_window(&gui, win);

    /* 窗口背景 / Window background */
    win->root.style.bg_color = egui_rgb888_to_rgb565(0x1A, 0x1A, 0x1A);

    /* 标题 / Title */
    egui_label_create(&win->root, "User Login",
        (egui_rect_t){120, 30, 240, 40});

    /* 用户名输入框 / Username input */
    egui_label_create(&win->root, "Username:",
        (egui_rect_t){50, 90, 100, 25});
    egui_widget_t *username_tb = egui_textbox_create(&win->root, form_data.username,
        sizeof(form_data.username), (egui_rect_t){160, 88, 270, 30});

    /* 密码输入框 / Password input */
    egui_label_create(&win->root, "Password:",
        (egui_rect_t){50, 130, 100, 25});
    egui_widget_t *password_tb = egui_textbox_create(&win->root, form_data.password,
        sizeof(form_data.password), (egui_rect_t){160, 128, 270, 30});

    /* 记住我 / Remember me */
    egui_widget_t *remember_cb = egui_checkbox_create(&win->root, "Remember me",
        false, (egui_rect_t){50, 175, 150, 25});
    remember_cb->on_event = remember_on_toggle;

    /* 接受条款 / Accept terms */
    egui_widget_t *terms_cb = egui_checkbox_create(&win->root, "Accept Terms",
        false, (egui_rect_t){50, 205, 150, 25));
    terms_cb->on_event = terms_on_toggle;

    /* 提交按钮 / Submit button */
    egui_widget_t *submit_btn = egui_button_create(&win->root, "Submit",
        (egui_rect_t){80, 245, 150, 40));
    submit_btn->on_event = submit_on_click;

    /* 取消按钮 / Cancel button */
    egui_widget_t *cancel_btn = egui_button_create(&win->root, "Cancel",
        (egui_rect_t){250, 245, 150, 40));
    cancel_btn->on_event = cancel_on_click;

    /* 状态标签 / Status label */
    egui_widget_t *status_label = egui_label_create(&win->root, form_status,
        (egui_rect_t){50, 290, 380, 25));

    /* 布局 / Layout */
    egui_layout_absolute(&win->root);

    /* 渲染 / Render */
    printf("Rendering form interface...\n");
    egui_widget_render(&win->root, &gui.fb);
    printf("Form interface rendered.\n");

    /* 模拟提交事件 / Simulate submit event */
    printf("\nSimulating form submission...\n");
    egui_event_t event = {
        .type = EGUI_EVENT_TOUCH_PRESS,
        .pos = {155, 265}, /* 在提交按钮上 / On submit button */
        .timestamp = 0,
    };
    egui_event_dispatch(&gui, &event);

    /* 重新渲染 / Re-render */
    egui_widget_render(&win->root, &gui.fb);
    printf("Form re-rendered with status update.\n");

    /* 清理 / Cleanup */
    egui_deinit(&gui);

    printf("\n=== Demo Complete ===\n");
    return 0;
}
