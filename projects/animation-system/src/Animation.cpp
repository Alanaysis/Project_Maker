#include "Animation.h"
#include <algorithm>
#include <cmath>

namespace anim {

Keyframe AnimationTrack::sample(float time) const {
    if (keyframes.empty()) {
        return Keyframe{};
    }

    // Single keyframe
    if (keyframes.size() == 1) {
        return keyframes[0];
    }

    // Clamp to range
    if (time <= keyframes.front().time) {
        return keyframes.front();
    }
    if (time >= keyframes.back().time) {
        return keyframes.back();
    }

    // Find surrounding keyframes
    for (size_t i = 0; i < keyframes.size() - 1; i++) {
        if (time >= keyframes[i].time && time <= keyframes[i + 1].time) {
            const Keyframe& k0 = keyframes[i];
            const Keyframe& k1 = keyframes[i + 1];

            // Calculate interpolation factor
            float duration = k1.time - k0.time;
            float t = (duration > 0.0f) ? (time - k0.time) / duration : 0.0f;

            // Interpolate
            Keyframe result;
            result.time = time;
            result.position = k0.position + (k1.position - k0.position) * t;
            result.rotation = Quat::slerp(k0.rotation, k1.rotation, t);
            result.scale = k0.scale + (k1.scale - k0.scale) * t;
            return result;
        }
    }

    return keyframes.back();
}

void AnimationClip::addTrack(const AnimationTrack& track) {
    tracks_.push_back(track);
}

AnimationTrack* AnimationClip::getTrack(const std::string& bone_name) {
    for (auto& track : tracks_) {
        if (track.bone_name == bone_name) {
            return &track;
        }
    }
    return nullptr;
}

const AnimationTrack* AnimationClip::getTrack(const std::string& bone_name) const {
    for (const auto& track : tracks_) {
        if (track.bone_name == bone_name) {
            return &track;
        }
    }
    return nullptr;
}

} // namespace anim
