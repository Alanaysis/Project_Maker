#pragma once

#include "MathTypes.h"
#include <vector>
#include <string>

namespace anim {

// A single keyframe for a bone
struct Keyframe {
    float time = 0.0f;        // Time in seconds
    Vec3 position;
    Quat rotation;
    Vec3 scale = {1, 1, 1};
};

// Animation track for a single bone
struct AnimationTrack {
    std::string bone_name;
    std::vector<Keyframe> keyframes;

    // Sample at given time
    Keyframe sample(float time) const;
};

// A complete animation clip
class AnimationClip {
public:
    AnimationClip() = default;
    AnimationClip(const std::string& name, float duration)
        : name_(name), duration_(duration) {}

    // Add a track for a bone
    void addTrack(const AnimationTrack& track);

    // Get track for a bone
    AnimationTrack* getTrack(const std::string& bone_name);
    const AnimationTrack* getTrack(const std::string& bone_name) const;

    // Get all tracks
    const std::vector<AnimationTrack>& getTracks() const { return tracks_; }

    // Get animation name
    const std::string& getName() const { return name_; }

    // Get duration in seconds
    float getDuration() const { return duration_; }

    // Set duration
    void setDuration(float duration) { duration_ = duration; }

    // Check if animation loops
    bool isLooping() const { return looping_; }
    void setLooping(bool loop) { looping_ = loop; }

private:
    std::string name_;
    float duration_ = 0.0f;
    bool looping_ = true;
    std::vector<AnimationTrack> tracks_;
};

} // namespace anim
