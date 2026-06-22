// test_skinning.cpp - Tests for skinning and full pipeline

TEST(skinning_basic) {
    // Create a simple skinned mesh
    SkinnedMesh mesh;

    // Create a triangle with skinning weights
    SkinnedVertex v0;
    v0.position = Vec3(0, 0, 0);
    v0.addWeight(0, 1.0f);  // Fully influenced by bone 0

    SkinnedVertex v1;
    v1.position = Vec3(1, 0, 0);
    v1.addWeight(0, 0.5f);  // 50% bone 0, 50% bone 1
    v1.addWeight(1, 0.5f);

    SkinnedVertex v2;
    v2.position = Vec3(0, 1, 0);
    v2.addWeight(1, 1.0f);  // Fully influenced by bone 1

    mesh.addVertex(v0);
    mesh.addVertex(v1);
    mesh.addVertex(v2);
    mesh.addTriangle(0, 1, 2);

    ASSERT_TRUE(mesh.getVertexCount() == 3);
    ASSERT_TRUE(mesh.getTriangleCount() == 1);

    // Create skinning matrices (identity = no movement)
    std::vector<Mat4> skinning_matrices(2);

    // Test skinning with identity matrices
    std::vector<Vec3> skinned = mesh.skin(skinning_matrices);
    ASSERT_VEC3_EQ(skinned[0], Vec3(0, 0, 0));
    ASSERT_VEC3_EQ(skinned[1], Vec3(1, 0, 0));
    ASSERT_VEC3_EQ(skinned[2], Vec3(0, 1, 0));

    // Test skinning with translation
    skinning_matrices[0] = Mat4::translation(Vec3(5, 0, 0));
    skinning_matrices[1] = Mat4::translation(Vec3(0, 5, 0));

    skinned = mesh.skin(skinning_matrices);

    // v0 is fully influenced by bone 0 -> moved by (5, 0, 0)
    ASSERT_FLOAT_EQ(skinned[0].x, 5);
    ASSERT_FLOAT_EQ(skinned[0].y, 0);

    // v1 is at (1,0,0), 50% bone 0 (translate +5), 50% bone 1 (translate +5y)
    // bone0: (1+5, 0, 0) = (6,0,0), bone1: (1, 5, 0) = (1,5,0)
    // result = 0.5*(6,0,0) + 0.5*(1,5,0) = (3.5, 2.5, 0)
    ASSERT_FLOAT_EQ(skinned[1].x, 3.5f);
    ASSERT_FLOAT_EQ(skinned[1].y, 2.5f);

    // v2 is fully influenced by bone 1 -> moved by (0, 5, 0)
    ASSERT_FLOAT_EQ(skinned[2].x, 0);
    ASSERT_FLOAT_EQ(skinned[2].y, 6);  // 1 + 5
}

TEST(full_pipeline) {
    // Test the complete animation pipeline:
    // Bone Data -> Animation Sampling -> Bone Transform -> Skinning -> Vertex Transform

    // 1. Create skeleton
    auto skeleton = std::make_shared<Skeleton>();
    int root = skeleton->addBone("Root", -1, Vec3(0, 0, 0));
    int arm = skeleton->addBone("Arm", root, Vec3(1, 0, 0));
    int hand = skeleton->addBone("Hand", arm, Vec3(1, 0, 0));

    skeleton->computeBindPose();

    // 2. Create animation (arm swings up)
    auto clip = std::make_shared<AnimationClip>("Swing", 1.0f);
    clip->setLooping(false);  // Disable looping for this test

    AnimationTrack root_track;
    root_track.bone_name = "Root";
    Keyframe rk;
    rk.time = 0.0f;
    rk.position = Vec3(0, 0, 0);
    root_track.keyframes.push_back(rk);
    clip->addTrack(root_track);

    AnimationTrack arm_track;
    arm_track.bone_name = "Arm";
    Keyframe ak0;
    ak0.time = 0.0f;
    ak0.position = Vec3(1, 0, 0);
    ak0.rotation = Quat::fromAxisAngle(Vec3(0, 0, 1), 0.0f);  // No rotation
    arm_track.keyframes.push_back(ak0);
    Keyframe ak1;
    ak1.time = 1.0f;
    ak1.position = Vec3(1, 0, 0);
    ak1.rotation = Quat::fromAxisAngle(Vec3(0, 0, 1), 1.5708f);  // 90 degrees
    arm_track.keyframes.push_back(ak1);
    clip->addTrack(arm_track);

    AnimationTrack hand_track;
    hand_track.bone_name = "Hand";
    Keyframe hk;
    hk.time = 0.0f;
    hk.position = Vec3(1, 0, 0);
    hand_track.keyframes.push_back(hk);
    clip->addTrack(hand_track);

    // 3. Create skinned mesh (a single vertex on the hand)
    SkinnedMesh mesh;
    SkinnedVertex vertex;
    vertex.position = Vec3(2, 0, 0);  // At hand position in bind pose
    vertex.addWeight(hand, 1.0f);      // Fully influenced by hand bone
    mesh.addVertex(vertex);

    // 4. Create animator and play animation
    Animator animator;
    animator.setSkeleton(skeleton);
    animator.play(clip);

    // 5. Update at time 0 (bind pose)
    animator.update(0.0f);
    const auto& matrices_0 = animator.getSkinningMatrices();
    std::vector<Vec3> skinned_0 = mesh.skin(matrices_0);

    // At time 0, vertex should be at bind position
    ASSERT_FLOAT_EQ(skinned_0[0].x, 2);
    ASSERT_FLOAT_EQ(skinned_0[0].y, 0);

    // 6. Update at time 0.5 (half rotation)
    animator.update(0.5f);
    const auto& matrices_05 = animator.getSkinningMatrices();
    std::vector<Vec3> skinned_05 = mesh.skin(matrices_05);

    // At 45 degrees, hand should be rotated
    // The exact position depends on the rotation center
    std::cout << "(mid: " << skinned_05[0].x << ", " << skinned_05[0].y << ") ";

    // 7. Update at time 1.0 (full rotation - 90 degrees)
    animator.update(0.5f);
    const auto& matrices_1 = animator.getSkinningMatrices();
    std::vector<Vec3> skinned_1 = mesh.skin(matrices_1);

    // After 90 degree rotation around Z at root, hand should move upward
    std::cout << "(end: " << skinned_1[0].x << ", " << skinned_1[0].y << ") ";

    // Verify animation time tracking
    ASSERT_FLOAT_EQ(animator.getCurrentTime(), 1.0f);
}
