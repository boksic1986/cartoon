from pathlib import Path

import pytest
from pydantic import ValidationError

from idiom_video.schemas import (
    AlignmentCue,
    ComfyUIDryRunJob,
    ComfyUISmokeCheckIssue,
    ComfyUISmokeCheckReport,
    IdiomProfile,
    LipSyncJob,
    ModelManifest,
    RealImagePreflightIssue,
    RealImagePreflightReport,
    RealVideoPreflightIssue,
    RealVideoPreflightReport,
    ReviewPacket,
    ReviewPacketItem,
    SeedanceCostEstimate,
    SeedanceDryRunJob,
    SeedanceSubmitPlan,
    SeedanceSubmitPlanItem,
    SeedanceTaskBatch,
    SeedanceTaskRecord,
    SeedanceTaskResult,
    SeedanceTaskResults,
    Storyboard,
    StoryboardScene,
    VideoMotionReview,
    VideoMotionReviewItem,
    VoiceJob,
)
from idiom_video.utils.json_io import read_json


FIXTURES = Path(__file__).parent / "fixtures"


def test_idiom_profile_loads_fixture():
    profile = IdiomProfile.model_validate(read_json(FIXTURES / "idiom_sample.json"))

    assert profile.slug == "shou-zhu-dai-tu"
    assert profile.characters[0].id == "farmer_amu"


def test_idiom_profile_requires_characters():
    data = read_json(FIXTURES / "idiom_sample.json")
    data["characters"] = []

    with pytest.raises(ValidationError):
        IdiomProfile.model_validate(data)


def test_storyboard_rejects_more_than_sixty_seconds():
    scene = StoryboardScene(
        scene_id="scene_01",
        order=1,
        title="Too long",
        visual_description="A long scene",
        camera="static",
        action="wait",
        duration_seconds=61,
        image_prompt_hint="field",
        video_prompt_hint="slow movement",
        speech_cues=[],
    )

    with pytest.raises(ValidationError):
        Storyboard(idiom_slug="x", title="x", scenes=[scene])


def test_speech_cue_keeps_lip_sync_disabled_by_default():
    storyboard = Storyboard.model_validate(read_json(FIXTURES / "storyboard_sample.json"))
    cue = storyboard.scenes[0].speech_cues[0]

    assert cue.lip_sync_required is False
    assert cue.mouth_action == "none"


def test_voice_alignment_and_lipsync_schemas_are_strict():
    voice_job = VoiceJob(
        job_id="voice_scene_01_narration",
        cue_id="scene_01_narration",
        scene_id="scene_01",
        speaker_id="narrator",
        speaker_name="旁白",
        text="很久以前，有个农夫叫阿木。",
        emotion="warm",
        start_seconds=0,
        end_seconds=3,
        output_path="outputs/story/audio/scene_01_narration.txt",
    )
    alignment = AlignmentCue(
        cue_id=voice_job.cue_id,
        scene_id=voice_job.scene_id,
        speaker_id=voice_job.speaker_id,
        text=voice_job.text,
        audio_path=voice_job.output_path,
        start_seconds=voice_job.start_seconds,
        end_seconds=voice_job.end_seconds,
        tokens=[],
    )
    lipsync_job = LipSyncJob(
        job_id="lipsync_scene_01_narration",
        cue_id=voice_job.cue_id,
        scene_id=voice_job.scene_id,
        audio_path=voice_job.output_path,
        alignment_path="outputs/story/07_alignment.json",
        enabled=False,
        reason="MVP 旁白不需要精确口型同步",
        output_path="outputs/story/lipsync/scene_01_narration.txt",
    )

    assert voice_job.provider == "mock"
    assert alignment.duration_seconds == 3
    assert lipsync_job.enabled is False

    payload = voice_job.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        VoiceJob.model_validate(payload)


def test_comfyui_dry_run_job_schema_is_strict():
    job = ComfyUIDryRunJob(
        dry_run_id="comfyui_image_scene_01",
        source_job_id="image_scene_01",
        scene_id="scene_01",
        workflow_path="workflows/comfyui/text2image_sdxl.placeholder.json",
        prompt="原创中国风儿童绘本动画",
        negative_prompt="no logo",
        seed=123,
        width=768,
        height=1344,
        intended_output_path="outputs/story/images_raw/scene_01.png",
        request_preview_path="outputs/story/comfyui_dry_run/scene_01.json",
    )

    assert job.provider == "comfyui"
    assert job.dry_run is True

    payload = job.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        ComfyUIDryRunJob.model_validate(payload)


def test_model_manifest_and_comfyui_smoke_report_schemas_are_strict():
    manifest = ModelManifest.model_validate(
        {
            "models": [
                {
                    "name": "idiom_story_sdxl_checkpoint",
                    "type": "checkpoint",
                    "local_path": "D:/ComfyUI/models/checkpoints/idiom_story_sdxl.safetensors",
                    "source": "manual_reviewed",
                    "license": "LICENSE_REVIEWED",
                    "commercial_use_allowed": True,
                    "notes": "人工审核记录。",
                }
            ]
        }
    )
    report = ComfyUISmokeCheckReport(
        ok=True,
        workflow_path="workflows/comfyui/text2image_reviewed.json",
        manifest_path="data/models/models_manifest.json",
        dry_run_jobs_path="outputs/story/comfyui_dry_run/jobs.json",
        checks={"workflow_json": "passed"},
        issues=[],
    )

    assert manifest.models[0].commercial_use_allowed is True
    assert report.issues == []

    payload = report.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        ComfyUISmokeCheckReport.model_validate(payload)

    with pytest.raises(ValidationError):
        ComfyUISmokeCheckIssue.model_validate({"message": "x", "unexpected": "reject"})


def test_seedance_dry_run_job_schema_is_strict():
    job = SeedanceDryRunJob(
        dry_run_id="seedance_video_scene_01",
        source_job_id="video_scene_01",
        scene_id="scene_01",
        image_path="outputs/story/images_approved/scene_01.png",
        prompt="温和推镜，人物轻微动作。",
        duration_seconds=5,
        intended_output_path="outputs/story/videos/scene_01.txt",
        request_preview_path="outputs/story/videos/scene_01.seedance_dry_run.json",
    )

    assert job.provider == "seedance"
    assert job.dry_run is True

    payload = job.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        SeedanceDryRunJob.model_validate(payload)


def test_review_packet_schema_is_strict():
    item = ReviewPacketItem(
        item_id="image_scene_01",
        item_type="image",
        scene_id="scene_01",
        title="镜头 scene_01 图片审核",
        artifact_paths=["outputs/story/images_approved/scene_01.png"],
        checklist=["角色一致", "无品牌标识"],
        status="approved",
        notes="mock 自动通过。",
    )
    packet = ReviewPacket(
        idiom_slug="shou-zhu-dai-tu",
        title="守株待兔",
        story_dir="outputs/story",
        items=[item],
        summary={"approved": 1, "pending": 0, "rejected": 0},
    )

    assert packet.items[0].item_type == "image"

    payload = packet.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        ReviewPacket.model_validate(payload)

    item_payload = item.model_dump(mode="json")
    item_payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        ReviewPacketItem.model_validate(item_payload)


def test_real_image_preflight_report_schema_is_strict():
    report = RealImagePreflightReport(
        ok=True,
        story_dir="outputs/story",
        workflow_path="workflows/comfyui/text2image_reviewed.json",
        manifest_path="data/models/models_manifest.json",
        smoke_report_path="outputs/story/quality_reports/comfyui_smoke_check.json",
        checks={"comfyui_smoke": "passed"},
        issues=[],
        next_step="STOP_BEFORE_REAL_IMAGE_GENERATION",
        stop_reason="Ready to generate real images; stop for user confirmation.",
    )

    assert report.ok is True

    payload = report.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        RealImagePreflightReport.model_validate(payload)

    with pytest.raises(ValidationError):
        RealImagePreflightIssue.model_validate({"message": "x", "unexpected": "reject"})


def test_video_motion_review_schema_is_strict():
    item = VideoMotionReviewItem(
        item_id="motion_scene_01",
        scene_id="scene_01",
        title="清晨耕田 运动审核",
        image_path="outputs/story/images_approved/scene_01.png",
        request_preview_path="outputs/story/videos/scene_01.seedance_dry_run.json",
        duration_seconds=5,
        motion_prompt="温和推镜，阿木抬头擦汗，固定背景连续性保持一致。",
        continuity_prompt_present=True,
        checklist=["首帧图片存在", "运动提示词保留固定背景连续性"],
        status="approved",
        notes="自动技术审核通过。",
    )
    review = VideoMotionReview(
        idiom_slug="shou-zhu-dai-tu",
        title="守株待兔",
        story_dir="outputs/story",
        seedance_dry_run_jobs_path="outputs/story/seedance_dry_run/jobs.json",
        auto=True,
        items=[item],
        summary={"approved": 1, "pending": 0, "rejected": 0},
    )

    assert review.items[0].continuity_prompt_present is True

    payload = review.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        VideoMotionReview.model_validate(payload)

    item_payload = item.model_dump(mode="json")
    item_payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        VideoMotionReviewItem.model_validate(item_payload)

    item_payload = item.model_dump(mode="json")
    item_payload["motion_prompt"] = "   "
    with pytest.raises(ValidationError):
        VideoMotionReviewItem.model_validate(item_payload)


def test_real_video_preflight_report_schema_is_strict():
    report = RealVideoPreflightReport(
        ok=True,
        story_dir="outputs/story",
        seedance_dry_run_jobs_path="outputs/story/seedance_dry_run/jobs.json",
        video_motion_review_path="outputs/story/review/video_motion_review.json",
        review_packet_path="outputs/story/review/review_packet.json",
        artifact_fingerprint="sha256:abc123",
        checks={"video_motion_review": "passed"},
        issues=[],
        next_step="STOP_BEFORE_REAL_VIDEO_GENERATION",
        stop_reason="Ready to generate real videos; stop for user confirmation.",
    )

    assert report.ok is True

    payload = report.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        RealVideoPreflightReport.model_validate(payload)

    with pytest.raises(ValidationError):
        RealVideoPreflightIssue.model_validate({"message": "x", "unexpected": "reject"})


def test_seedance_cost_estimate_schema_is_strict():
    estimate = SeedanceCostEstimate(
        provider="seedance",
        model_name="Dreamina-Seedance-2.0",
        billing_mode="input_without_video",
        currency="USD",
        unit_price_per_million_tokens=7,
        retry_multiplier=1.2,
        width=864,
        height=496,
        fps=24,
        clip_count=10,
        total_duration_seconds=51,
        estimated_tokens=512244,
        base_cost=3.586,
        estimated_total_cost=4.3032,
        story_dir="outputs/story",
        video_jobs_path="outputs/story/05_video_jobs.json",
        video_jobs_fingerprint="sha256:abc123",
        price_source="manual price",
        price_source_url="https://docs.byteplus.com/docs/ModelArk/1099320",
        price_checked_at="2026-05-03",
        notes=["offline estimate only"],
    )

    assert estimate.provider == "seedance"

    payload = estimate.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        SeedanceCostEstimate.model_validate(payload)


def test_seedance_submit_plan_schema_is_strict():
    item = SeedanceSubmitPlanItem(
        source_job_id="video_scene_01",
        scene_id="scene_01",
        image_path="outputs/story/images_approved/scene_01.png",
        prompt="slow push in",
        duration_seconds=5,
        intended_output_path="outputs/story/videos/scene_01.mp4",
        request_preview_path="outputs/story/videos/scene_01.seedance_dry_run.json",
        status="ready",
    )
    plan = SeedanceSubmitPlan(
        ok=True,
        provider="seedance",
        dry_run=True,
        execute_real_requested=False,
        external_call_confirmed=True,
        story_dir="outputs/story",
        preflight_report_path="outputs/story/quality_reports/real_video_preflight.json",
        preflight_artifact_fingerprint="sha256:abc123",
        cost_estimate_path="outputs/story/quality_reports/seedance_cost_estimate.json",
        currency="USD",
        estimated_total_cost=4.3028,
        max_cost=5,
        item_count=1,
        items=[item],
        next_step="STOP_BEFORE_REAL_SEEDANCE_SUBMIT",
        stop_reason="Stop before real Seedance submit.",
        notes=["offline submit plan only"],
    )

    assert plan.items[0].status == "ready"

    payload = plan.model_dump(mode="json")
    payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        SeedanceSubmitPlan.model_validate(payload)

    item_payload = item.model_dump(mode="json")
    item_payload["unexpected"] = "reject"
    with pytest.raises(ValidationError):
        SeedanceSubmitPlanItem.model_validate(item_payload)


def test_seedance_task_lifecycle_schemas_are_strict():
    task = SeedanceTaskRecord(
        task_id="mock_scene_01",
        source_job_id="video_scene_01",
        scene_id="scene_01",
        image_path="outputs/story/images_approved/scene_01.png",
        prompt="slow push in",
        duration_seconds=5,
        intended_output_path="outputs/story/videos/scene_01.mp4",
        request_preview_path="outputs/story/videos/scene_01.seedance_dry_run.json",
        submit_request_path="outputs/story/seedance_tasks/scene_01.submit_request.json",
        submit_response_path="outputs/story/seedance_tasks/scene_01.submit_response.json",
        status="submitted",
    )
    batch = SeedanceTaskBatch(
        ok=True,
        provider="seedance",
        client="mock",
        dry_run=True,
        submit_plan_path="outputs/story/seedance_submit/submit_plan.json",
        submit_plan_fingerprint="sha256:abc123",
        task_count=1,
        tasks=[task],
        next_step="MOCK_POLL_SEEDANCE_TASKS",
    )
    result = SeedanceTaskResult(
        task_id="mock_scene_01",
        source_job_id="video_scene_01",
        scene_id="scene_01",
        status="succeeded",
        output_path="outputs/story/videos/scene_01.seedance_mock.txt",
        poll_response_path="outputs/story/seedance_tasks/scene_01.poll_response.json",
        download_response_path="outputs/story/seedance_tasks/scene_01.download_response.json",
        duration_seconds=5,
        provider="seedance_mock",
    )
    results = SeedanceTaskResults(
        ok=True,
        provider="seedance",
        client="mock",
        dry_run=True,
        submit_plan_path="outputs/story/seedance_submit/submit_plan.json",
        submit_plan_fingerprint="sha256:abc123",
        submissions_path="outputs/story/seedance_tasks/submissions.json",
        task_count=1,
        results=[result],
        next_step="MOCK_SEEDANCE_COMPLETE",
    )

    assert batch.tasks[0].status == "submitted"
    assert results.results[0].status == "succeeded"

    for model in (task, batch, result, results):
        payload = model.model_dump(mode="json")
        payload["unexpected"] = "reject"
        with pytest.raises(ValidationError):
            type(model).model_validate(payload)
