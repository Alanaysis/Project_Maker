// test_animation.cpp - Tests for animation sampling and blending

TEST(animation_sampling) {
    // Create animation track
    AnimationTrack track;
    track.bone_name = "TestBone";

    // Add keyframes
    Keyframe k0;
    k0.time = 0.0f;
    k0.position = Vec3(0, 0, 0);
    k0.rotation = Quat::fromAxisAngle(Vec3(0, 1, 0), 0.0f);
    track.keyframes.push_back(k0);

    Keyframe k1;
    k1.time = 1.0f;
    k1.position = Vec3(10, 0, 0);
    k1.rotation = Quat::fromAxisAngle(Vec3(0, 1, 0), 1.5708f); // 90 degrees
    track.keyframes.push_back(k1);

    // Test sampling at start
    Keyframe s0 = track.sample(0.0f);
    ASSERT_FLOAT_EQ(s0.position.x, 0);
    ASSERT_FLOAT_EQ(s0.time, 0.0f);

    // Test sampling at end
    Keyframe s1 = track.sample(1.0f);
    ASSERT_FLOAT_EQ(s1.position.x, 10);
    ASSERT_FLOAT_EQ(s1.time, 1.0f);

    // Test sampling at middle
    Keyframe s_mid = track.sample(0.5f);
    ASSERT_FLOAT_EQ(s_mid.position.x, 5);
    ASSERT_FLOAT_EQ(s_mid.time, 0.5f);

    // Test sampling before start
    Keyframe s_before = track.sample(-1.0f);
    ASSERT_FLOAT_EQ(s_before.position.x, 0);

    // Test sampling after end
    Keyframe s_after = track.sample(2.0f);
    ASSERT_FLOAT_EQ(s_after.position.x, 10);

    // Test multiple keyframes
    AnimationTrack track3;
    track3.bone_name = "MultiBone";

    Keyframe mk0;
    mk0.time = 0.0f;
    mk0.position = Vec3(0, 0, 0);
    track3.keyframes.push_back(mk0);

    Keyframe mk1;
    mk1.time = 1.0f;
    mk1.position = Vec3(10, 0, 0);
    track3.keyframes.push_back(mk1);

    Keyframe mk2;
    mk2.time = 2.0f;
    mk2.position = Vec3(10, 10, 0);
    track3.keyframes.push_back(mk2);

    // Sample between second and third keyframe
    Keyframe s_15 = track3.sample(1.5f);
    ASSERT_FLOAT_EQ(s_15.position.x, 10);
    ASSERT_FLOAT_EQ(s_15.position.y, 5);

    // Create animation clip
    AnimationClip clip("Walk", 2.0f);
    clip.addTrack(track);
    clip.addTrack(track3);

    ASSERT_TRUE(clip.getName() == "Walk");
    ASSERT_FLOAT_EQ(clip.getDuration(), 2.0f);
    ASSERT_TRUE(clip.getTracks().size() == 2);

    // Get track by name
    AnimationTrack* found = clip.getTrack("TestBone");
    ASSERT_TRUE(found != nullptr);
    ASSERT_TRUE(found->bone_name == "TestBone");
}

TEST(animation_blending) {
    // Create two animation clips
    auto clip_a = std::make_shared<AnimationClip>("Idle", 1.0f);
    auto clip_b = std::make_shared<AnimationClip>("Walk", 1.0f);

    // Add track to clip A
    AnimationTrack track_a;
    track_a.bone_name = "Root";
    Keyframe ka;
    ka.time = 0.0f;
    ka.position = Vec3(0, 0, 0);
    track_a.keyframes.push_back(ka);
    clip_a->addTrack(track_a);

    // Add track to clip B
    AnimationTrack track_b;
    track_b.bone_name = "Root";
    Keyframe kb;
    kb.time = 0.0f;
    kb.position = Vec3(10, 0, 0);
    track_b.keyframes.push_back(kb);
    clip_b->addTrack(track_b);

    // Create blender
    AnimationBlender blender;
    blender.setClipA(clip_a);
    blender.setClipB(clip_b);

    // Test blend factor 0 (full A)
    blender.setBlendFactor(0.0f);
    Keyframe result_0 = blender.sample("Root", 0.0f);
    ASSERT_FLOAT_EQ(result_0.position.x, 0);

    // Test blend factor 1 (full B)
    blender.setBlendFactor(1.0f);
    Keyframe result_1 = blender.sample("Root", 0.0f);
    ASSERT_FLOAT_EQ(result_1.position.x, 10);

    // Test blend factor 0.5 (half way)
    blender.setBlendFactor(0.5f);
    Keyframe result_5 = blender.sample("Root", 0.0f);
    ASSERT_FLOAT_EQ(result_5.position.x, 5);
}
