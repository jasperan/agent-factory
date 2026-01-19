"""Quick validation test for core models"""

from core.models import (
    PLCAtom,
    RIVETAtom,
    Module,
    Course,
    VideoScript,
    UploadJob,
    EducationalLevel,
    RootCause,
    CorrectiveAction,
)


def test_plc_atom():
    """Test PLCAtom creation and validation"""
    atom = PLCAtom(
        id="plc:generic:ohms-law",
        title="Ohm's Law: V=I×R",
        description="The fundamental relationship between voltage, current, and resistance in electrical circuits.",
        keywords=["ohms law", "electricity", "V=IR"],
        educational_level=EducationalLevel.INTRO,
        learning_resource_type="explanation",
        typical_learning_time_minutes=10,
        domain="electricity",
        vendor="generic",
        prerequisites=["plc:generic:voltage", "plc:generic:current", "plc:generic:resistance"],
        learning_objectives=[
            "Calculate voltage given current and resistance",
            "Calculate current given voltage and resistance",
        ]
    )
    assert atom.id == "plc:generic:ohms-law"
    assert atom.domain == "electricity"
    assert len(atom.prerequisites) == 3
    print(f"PASS: PLCAtom validation - {atom.title}")
    return atom


def test_rivet_atom():
    """Test RIVETAtom creation and validation"""
    atom = RIVETAtom(
        id="rivet:motor:won-t-start",
        title="3-Phase Motor Won't Start",
        description="Troubleshooting guide for motors that hum but don't rotate",
        educational_level=EducationalLevel.INTERMEDIATE,
        learning_resource_type="troubleshooting",
        typical_learning_time_minutes=20,
        equipment_class="ac_induction_motor",
        manufacturer="Generic",
        symptoms=["Motor hums but doesn't rotate", "Contactor energizes but motor doesn't start"],
        root_causes=[
            RootCause(
                cause="Single-phase condition (one leg of 3-phase power lost)",
                likelihood="common",
                verification="Measure voltage at motor terminals (expect 3-phase balanced)"
            ),
        ],
        diagnostic_steps=[
            "Verify power at disconnect (expect 480VAC 3-phase)",
            "Check contactor operation",
            "Measure voltage at motor terminals",
        ],
        corrective_actions=[
            CorrectiveAction(
                action="Replace blown fuse or reset tripped breaker",
                difficulty="easy",
                estimated_time_minutes=15,
                tools_required=["Multimeter", "Replacement fuse"],
                safety_warnings=["Lockout/tagout required", "Verify de-energized before touching"]
            ),
        ],
        safety_level="danger",
        lockout_tagout_required=True,
        constraints=["Equipment must be de-energized", "Lockout/tagout procedure required"],
        validation_stage=3,
    )
    assert atom.id == "rivet:motor:won-t-start"
    assert atom.safety_level == "danger"
    assert atom.lockout_tagout_required is True
    print(f"PASS: RIVETAtom validation - {atom.title}")
    return atom


def test_module():
    """Test Module creation and validation"""
    module = Module(
        id="module:electrical-fundamentals",
        title="Electrical Fundamentals",
        description="Core electricity concepts from voltage to power calculations",
        atom_ids=[
            "plc:generic:voltage",
            "plc:generic:current",
            "plc:generic:resistance",
            "plc:generic:ohms-law",
            "plc:generic:power",
        ],
        educational_level=EducationalLevel.INTRO,
        estimated_hours=2.5,
    )
    assert len(module.atom_ids) == 5
    assert module.estimated_hours == 2.5
    print(f"PASS: Module validation - {module.title}")
    return module


def test_course():
    """Test Course creation and validation"""
    course = Course(
        id="course:intro-to-plc",
        title="Introduction to PLC Programming",
        description="Complete beginner course from electricity basics to your first PLC program",
        module_ids=["module:electrical-fundamentals", "module:plc-basics"],
        estimated_hours=10.0,
        price_usd=49.99,
    )
    assert len(course.module_ids) == 2
    assert course.price_usd == 49.99
    print(f"PASS: Course validation - {course.title}")
    return course


def test_video_script():
    """Test VideoScript creation and validation"""
    script = VideoScript(
        id="script:ohms-law-video",
        title="Ohm's Law - The Foundation of Electrical Engineering (#3)",
        description="Master Ohm's Law (V=I×R) with clear explanations and real-world examples",
        outline=[
            "Hook: This one equation solves 90% of electrical problems",
            "What is Ohm's Law?",
            "Example calculation",
            "Recap and quiz",
        ],
        script_text="[enthusiastic] This one equation solves 90% of electrical problems. Today we're learning Ohm's Law, the most fundamental relationship in electricity. By the end of this video, you'll be able to calculate voltage, current, and resistance in any circuit. Let's get started!",
        atom_ids=["plc:generic:ohms-law"],
        educational_level=EducationalLevel.INTRO,
        duration_minutes=8,
        keywords=["ohms law", "V=IR", "electrical calculations"],
        tags=["ohms law", "electricity", "tutorial"],
        status="draft",
    )
    assert script.duration_minutes == 8
    assert len(script.outline) == 4
    print(f"PASS: VideoScript validation - {script.title}")
    return script


def test_upload_job():
    """Test UploadJob creation and validation"""
    job = UploadJob(
        id="upload:ohms-law-video",
        channel="industrial_skills_hub",
        video_script_id="script:ohms-law-video",
        audio_path="/media/ohms-law-audio.mp3",
        video_path="/media/ohms-law-video.mp4",
        thumbnail_path="/media/ohms-law-thumb.jpg",
        youtube_title="Ohm's Law - The Foundation of Electrical Engineering (#3)",
        youtube_description="Master Ohm's Law in 8 minutes...",
        tags=["ohms law", "electricity", "tutorial"],
        playlist_ids=["PLxxxxxx_ElectricalFundamentals"],
        visibility="public",
        status="pending",
    )
    assert job.channel == "industrial_skills_hub"
    assert job.visibility == "public"
    print(f"PASS: UploadJob validation - {job.youtube_title}")
    return job


def run_all_tests():
    """Run all model validation tests"""
    print("=" * 60)
    print("Core Models Validation Test Suite")
    print("=" * 60)

    test_plc_atom()
    test_rivet_atom()
    test_module()
    test_course()
    test_video_script()
    test_upload_job()

    print("=" * 60)
    print("All tests passed! Models are valid.")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
