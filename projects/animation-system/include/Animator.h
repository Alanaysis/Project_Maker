#pragma once

#include "Animation.h"
#include "Skeleton.h"
#include <memory>
#include <vector>

namespace anim {

// Animator plays animations and updates skeleton
class Animator {
public:
    Animator() = default;

    // Set the skeleton to animate
    void setSkeleton(std::shared_ptr<Skeleton> skeleton);

    // Get the skeleton
    std::shared_ptr<Skeleton> getSkeleton() const { return skeleton_; }

    // Play an animation clip
    void play(std::shared_ptr<AnimationClip> clip);

    // Update animation by delta time
    void update(float deltaTime);

    // Get current time
    float getCurrentTime() const { return current_time_; }

    // Set time directly
    void setTime(float time);

    // Get current clip
    std::shared_ptr<AnimationClip> getCurrentClip() const { return current_clip_; }

    // Get skinning matrices for rendering
    const std::vector<Mat4>& getSkinningMatrices() const { return skinning_matrices_; }

private:
    // Apply sampled animation to skeleton
    void applyAnimation();

    std::shared_ptr<Skeleton> skeleton_;
    std::shared_ptr<AnimationClip> current_clip_;
    float current_time_ = 0.0f;
    std::vector<Mat4> skinning_matrices_;
};

// Simple animation blending between two clips
class AnimationBlender {
public:
    AnimationBlender() = default;

    // Set clips to blend
    void setClipA(std::shared_ptr<AnimationClip> clip) { clip_a_ = clip; }
    void setClipB(std::shared_ptr<AnimationClip> clip) { clip_b_ = clip; }

    // Set blend factor (0.0 = full A, 1.0 = full B)
    void setBlendFactor(float factor) { blend_factor_ = factor; }
    float getBlendFactor() const { return blend_factor_; }

    // Sample blended animation at given time
    Keyframe sample(const std::string& bone_name, float time) const;

private:
    std::shared_ptr<AnimationClip> clip_a_;
    std::shared_ptr<AnimationClip> clip_b_;
    float blend_factor_ = 0.0f;
};

} // namespace anim
