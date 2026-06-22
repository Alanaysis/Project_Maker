#include "Animator.h"
#include <algorithm>

namespace anim {

void Animator::setSkeleton(std::shared_ptr<Skeleton> skeleton) {
    skeleton_ = skeleton;
}

void Animator::play(std::shared_ptr<AnimationClip> clip) {
    current_clip_ = clip;
    current_time_ = 0.0f;
}

void Animator::update(float deltaTime) {
    if (!current_clip_ || !skeleton_) return;

    current_time_ += deltaTime;

    // Handle looping
    if (current_clip_->isLooping() && current_clip_->getDuration() > 0.0f) {
        while (current_time_ >= current_clip_->getDuration()) {
            current_time_ -= current_clip_->getDuration();
        }
    } else {
        current_time_ = std::min(current_time_, current_clip_->getDuration());
    }

    // Apply animation
    applyAnimation();

    // Compute skinning matrices
    skeleton_->computeSkinningMatrices(skinning_matrices_);
}

void Animator::setTime(float time) {
    current_time_ = time;
    if (current_clip_ && skeleton_) {
        applyAnimation();
        skeleton_->computeSkinningMatrices(skinning_matrices_);
    }
}

void Animator::applyAnimation() {
    if (!current_clip_ || !skeleton_) return;

    // Sample each track and apply to skeleton
    for (const auto& track : current_clip_->getTracks()) {
        Bone* bone = skeleton_->getBone(track.bone_name);
        if (!bone) continue;

        Keyframe sampled = track.sample(current_time_);
        bone->local_position = sampled.position;
        bone->local_rotation = sampled.rotation;
        bone->local_scale = sampled.scale;
    }
}

Keyframe AnimationBlender::sample(const std::string& bone_name, float time) const {
    if (!clip_a_ || !clip_b_) {
        return Keyframe{};
    }

    const AnimationTrack* track_a = clip_a_->getTrack(bone_name);
    const AnimationTrack* track_b = clip_b_->getTrack(bone_name);

    Keyframe ka = track_a ? track_a->sample(time) : Keyframe{};
    Keyframe kb = track_b ? track_b->sample(time) : Keyframe{};

    // Blend keyframes
    Keyframe result;
    result.time = time;
    result.position = ka.position + (kb.position - ka.position) * blend_factor_;
    result.rotation = Quat::slerp(ka.rotation, kb.rotation, blend_factor_);
    result.scale = ka.scale + (kb.scale - ka.scale) * blend_factor_;

    return result;
}

} // namespace anim
