// test_skeleton.cpp - Tests for math types and skeleton

TEST(math_types) {
    // Test Vec3 operations
    Vec3 a(1, 2, 3);
    Vec3 b(4, 5, 6);
    Vec3 c = a + b;
    ASSERT_FLOAT_EQ(c.x, 5);
    ASSERT_FLOAT_EQ(c.y, 7);
    ASSERT_FLOAT_EQ(c.z, 9);

    Vec3 d = b - a;
    ASSERT_FLOAT_EQ(d.x, 3);
    ASSERT_FLOAT_EQ(d.y, 3);
    ASSERT_FLOAT_EQ(d.z, 3);

    Vec3 e = a * 2.0f;
    ASSERT_FLOAT_EQ(e.x, 2);
    ASSERT_FLOAT_EQ(e.y, 4);
    ASSERT_FLOAT_EQ(e.z, 6);

    // Test dot product
    float dot = a.dot(b);
    ASSERT_FLOAT_EQ(dot, 32); // 1*4 + 2*5 + 3*6 = 32

    // Test cross product
    Vec3 cross = a.cross(b);
    ASSERT_FLOAT_EQ(cross.x, -3);  // 2*6 - 3*5 = -3
    ASSERT_FLOAT_EQ(cross.y, 6);   // 3*4 - 1*6 = 6
    ASSERT_FLOAT_EQ(cross.z, -3);  // 1*5 - 2*4 = -3

    // Test length
    Vec3 f(3, 4, 0);
    ASSERT_FLOAT_EQ(f.length(), 5.0f);

    // Test Mat4
    Mat4 identity;
    Vec3 p(1, 2, 3);
    Vec3 result = identity.transformPoint(p);
    ASSERT_VEC3_EQ(result, p);

    // Test translation
    Mat4 trans = Mat4::translation(Vec3(10, 20, 30));
    Vec3 translated = trans.transformPoint(p);
    ASSERT_FLOAT_EQ(translated.x, 11);
    ASSERT_FLOAT_EQ(translated.y, 22);
    ASSERT_FLOAT_EQ(translated.z, 33);
}

TEST(quaternion) {
    // Test identity quaternion
    Quat identity;
    Vec3 v(1, 2, 3);
    Vec3 rotated = identity.rotate(v);
    ASSERT_VEC3_EQ(rotated, v);

    // Test 90 degree rotation around Y axis
    Quat rot90y = Quat::fromAxisAngle(Vec3(0, 1, 0), 3.14159f / 2.0f);
    Vec3 x_axis(1, 0, 0);
    Vec3 rotated_x = rot90y.rotate(x_axis);
    ASSERT_FLOAT_EQ(rotated_x.x, 0.0f);
    ASSERT_FLOAT_EQ(rotated_x.y, 0.0f);
    ASSERT_FLOAT_EQ(rotated_x.z, -1.0f);

    // Test quaternion multiplication
    Quat q1 = Quat::fromAxisAngle(Vec3(0, 1, 0), 1.0f);
    Quat q2 = Quat::fromAxisAngle(Vec3(0, 1, 0), 2.0f);
    Quat q3 = q1 * q2;
    Quat q_expected = Quat::fromAxisAngle(Vec3(0, 1, 0), 3.0f);
    ASSERT_FLOAT_EQ(q3.w, q_expected.w);
    ASSERT_FLOAT_EQ(q3.x, q_expected.x);

    // Test slerp
    Quat a = Quat::fromAxisAngle(Vec3(0, 1, 0), 0.0f);
    Quat b = Quat::fromAxisAngle(Vec3(0, 1, 0), 1.0f);
    Quat mid = Quat::slerp(a, b, 0.5f);
    Quat expected_mid = Quat::fromAxisAngle(Vec3(0, 1, 0), 0.5f);
    ASSERT_FLOAT_EQ(std::abs(mid.w), std::abs(expected_mid.w));
}

TEST(skeleton_basic) {
    Skeleton skeleton;

    // Add root bone
    int root_id = skeleton.addBone("Root", -1, Vec3(0, 0, 0));
    ASSERT_TRUE(root_id == 0);

    // Add child bone
    int child_id = skeleton.addBone("Spine", root_id, Vec3(0, 1, 0));
    ASSERT_TRUE(child_id == 1);

    // Check bone count
    ASSERT_TRUE(skeleton.getBoneCount() == 2);

    // Get bone by name
    Bone* root = skeleton.getBone("Root");
    ASSERT_TRUE(root != nullptr);
    ASSERT_TRUE(root->id == 0);

    Bone* spine = skeleton.getBone("Spine");
    ASSERT_TRUE(spine != nullptr);
    ASSERT_TRUE(spine->parent_id == 0);

    // Get bone by ID
    Bone* bone0 = skeleton.getBone(0);
    ASSERT_TRUE(bone0 != nullptr);
    ASSERT_TRUE(bone0->name == "Root");
}

TEST(skeleton_hierarchy) {
    Skeleton skeleton;

    // Build a simple humanoid skeleton
    int root = skeleton.addBone("Root", -1, Vec3(0, 0, 0));
    int spine = skeleton.addBone("Spine", root, Vec3(0, 1, 0));
    int head = skeleton.addBone("Head", spine, Vec3(0, 1.5, 0));
    int left_arm = skeleton.addBone("LeftArm", spine, Vec3(-1, 1.2, 0));
    int right_arm = skeleton.addBone("RightArm", spine, Vec3(1, 1.2, 0));

    ASSERT_TRUE(skeleton.getBoneCount() == 5);

    // Compute bind pose
    skeleton.computeBindPose();

    // Check world transforms
    std::vector<Mat4> world_matrices;
    skeleton.computeWorldTransforms(world_matrices);

    // Root should be at origin
    Vec3 root_pos = world_matrices[root].transformPoint(Vec3(0, 0, 0));
    ASSERT_FLOAT_EQ(root_pos.x, 0);
    ASSERT_FLOAT_EQ(root_pos.y, 0);

    // Spine should be at (0, 1, 0)
    Vec3 spine_pos = world_matrices[spine].transformPoint(Vec3(0, 0, 0));
    ASSERT_FLOAT_EQ(spine_pos.x, 0);
    ASSERT_FLOAT_EQ(spine_pos.y, 1);

    // Head should be at (0, 2.5, 0) (1 + 1.5)
    Vec3 head_pos = world_matrices[head].transformPoint(Vec3(0, 0, 0));
    ASSERT_FLOAT_EQ(head_pos.x, 0);
    ASSERT_FLOAT_EQ(head_pos.y, 2.5f);
}
