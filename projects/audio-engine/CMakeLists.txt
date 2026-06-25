cmake_minimum_required(VERSION 3.16)
project(audio-engine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# ============================================================================
# 基础模块
# ============================================================================

add_executable(basic_sampling src/basic/sampling.cpp)
add_executable(basic_quantization src/basic/quantization.cpp)
add_executable(basic_sample_rate src/basic/sample_rate.cpp)
add_executable(basic_bit_depth src/basic/bit_depth.cpp)
add_executable(basic_channels src/basic/channels.cpp)

# ============================================================================
# 编解码模块
# ============================================================================

add_executable(pcm_codec src/codec/pcm_codec.cpp)
add_executable(wav_codec src/codec/wav_codec.cpp)
add_executable(mp3_codec src/codec/mp3_codec.cpp)
add_executable(aac_codec src/codec/aac_codec.cpp)
add_executable(opus_codec src/codec/opus_codec.cpp)

# ============================================================================
# 音频处理模块
# ============================================================================

add_executable(processing_volume src/processing/volume.cpp)
add_executable(processing_fade src/processing/fade.cpp)
add_executable(processing_mixer src/processing/mixer.cpp)
add_executable(processing_equalizer src/processing/equalizer.cpp)
add_executable(processing_compressor src/processing/compressor.cpp)
add_executable(processing_limiter src/processing/limiter.cpp)

# ============================================================================
# 音频效果模块
# ============================================================================

add_executable(effects_reverb src/effects/reverb.cpp)
add_executable(effects_delay src/effects/delay.cpp)
add_executable(effects_chorus src/effects/chorus.cpp)
add_executable(effects_distortion src/effects/distortion.cpp)
add_executable(effects_noise_reduction src/effects/noise_reduction.cpp)

# ============================================================================
# 音频分析模块
# ============================================================================

add_executable(analysis_fft src/analysis/fft.cpp)
add_executable(analysis_spectrum src/analysis/spectrum.cpp)
add_executable(analysis_rhythm src/analysis/rhythm.cpp)
add_executable(analysis_pitch src/analysis/pitch.cpp)
add_executable(analysis_features src/analysis/features.cpp)

# ============================================================================
# 音频合成模块
# ============================================================================

add_executable(synthesis_waveform src/synthesis/waveform.cpp)
add_executable(synthesis_fm src/synthesis/fm_synth.cpp)
add_executable(synthesis_subtractive src/synthesis/subtractive.cpp)
add_executable(synthesis_sampler src/synthesis/sampler.cpp)

# ============================================================================
# 实际应用模块
# ============================================================================

add_executable(app_player src/apps/audio_player.cpp)
add_executable(app_editor src/apps/audio_editor.cpp)
add_executable(app_analyzer src/apps/analyzer.cpp)
add_executable(app_synthesizer src/apps/synthesizer.cpp)

# ============================================================================
# 链接数学库（Linux）
# ============================================================================

if(UNIX AND NOT APPLE)
    target_link_libraries(basic_sampling m)
    target_link_libraries(basic_quantization m)
    target_link_libraries(basic_sample_rate m)
    target_link_libraries(basic_bit_depth m)
    target_link_libraries(basic_channels m)
    target_link_libraries(pcm_codec m)
    target_link_libraries(wav_codec m)
    target_link_libraries(mp3_codec m)
    target_link_libraries(aac_codec m)
    target_link_libraries(opus_codec m)
    target_link_libraries(processing_volume m)
    target_link_libraries(processing_fade m)
    target_link_libraries(processing_mixer m)
    target_link_libraries(processing_equalizer m)
    target_link_libraries(processing_compressor m)
    target_link_libraries(processing_limiter m)
    target_link_libraries(effects_reverb m)
    target_link_libraries(effects_delay m)
    target_link_libraries(effects_chorus m)
    target_link_libraries(effects_distortion m)
    target_link_libraries(effects_noise_reduction m)
    target_link_libraries(analysis_fft m)
    target_link_libraries(analysis_spectrum m)
    target_link_libraries(analysis_rhythm m)
    target_link_libraries(analysis_pitch m)
    target_link_libraries(analysis_features m)
    target_link_libraries(synthesis_waveform m)
    target_link_libraries(synthesis_fm m)
    target_link_libraries(synthesis_subtractive m)
    target_link_libraries(synthesis_sampler m)
    target_link_libraries(app_player m)
    target_link_libraries(app_editor m)
    target_link_libraries(app_analyzer m)
    target_link_libraries(app_synthesizer m)
endif()

# ============================================================================
# 安装
# ============================================================================

install(TARGETS
    basic_sampling basic_quantization basic_sample_rate basic_bit_depth basic_channels
    pcm_codec wav_codec mp3_codec aac_codec opus_codec
    processing_volume processing_fade processing_mixer processing_equalizer processing_compressor processing_limiter
    effects_reverb effects_delay effects_chorus effects_distortion effects_noise_reduction
    analysis_fft analysis_spectrum analysis_rhythm analysis_pitch analysis_features
    synthesis_waveform synthesis_fm synthesis_subtractive synthesis_sampler
    app_player app_editor app_analyzer app_synthesizer
    RUNTIME DESTINATION bin
)
