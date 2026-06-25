# ============================================================================
# Sanitizer 配置
# ============================================================================

function(enable_sanitizers target_name)
    if(MYPROJECT_ENABLE_ASAN)
        target_compile_options(${target_name} PRIVATE -fsanitize=address -fno-omit-frame-pointer)
        target_link_options(${target_name} PRIVATE -fsanitize=address)
        message(STATUS "AddressSanitizer enabled for ${target_name}")
    endif()

    if(MYPROJECT_ENABLE_UBSAN)
        target_compile_options(${target_name} PRIVATE -fsanitize=undefined)
        target_link_options(${target_name} PRIVATE -fsanitize=undefined)
        message(STATUS "UndefinedBehaviorSanitizer enabled for ${target_name}")
    endif()

    if(MYPROJECT_ENABLE_TSAN)
        target_compile_options(${target_name} PRIVATE -fsanitize=thread)
        target_link_options(${target_name} PRIVATE -fsanitize=thread)
        message(STATUS "ThreadSanitizer enabled for ${target_name}")
    endif()
endfunction()
