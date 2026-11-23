"""Replay the manually checked video observations without rewriting v0.9."""

import argparse
import copy
import hashlib
from pathlib import Path

from chuchariot.dataset_io import ROOT, TABLES, read_json, write_json
from chuchariot.validation import validate


VIDEO_SHA256 = "a107003c1f48c3f7bc9005379faa2f5db56760a122c4891cbd15c52a42d5a421"
OUTPUT = ROOT / "data/candidates/knowledge.v0.10.json"
ONTOLOGY = ROOT / "data/ontology/ontology.v0.6.json"
CASES = [
    {
        "key": "wheel-assembly", "label": "视频复原案例：车轮拼装",
        "start": 1564, "end": 1612, "transcription": "video_frame",
        "locator": "26:04—26:52，重点帧26:16、26:41、26:46；轮辋与辐条对位、敲合",
        "quote": "画面观察：复原者将辐条端部与轮辋孔对位，并在拼装中使用木槌敲合。",
        "value": "片中现代复原实验展示辐条与轮辋对位、敲合的车轮拼装过程。",
        "types": ["type:001", "type:004", "type:005"],
    },
    {
        "key": "tenon-explanation", "label": "视频复原推测：长短榫与装配便利性",
        "start": 1528, "end": 1606, "transcription": "video_subtitle",
        "locator": "25:28—26:46，25:28讲解辐条照片，26:11字幕说明复原者的解释",
        "quote": "26:11英文字幕：I think that is a way of making it easier to assemble the wheel.",
        "value": "片中复原者将辐条外端榫头的长短差异解释为便于分批对位、装配轮辋的做法，并在现代复原中演示；这是对设计意图的推测。",
        "types": ["type:004", "type:005"], "origin": "hypothesis",
        "rationale": "复原者以“I think”提出解释；装配演示为可行性参考，尚不能排除其他设计目的，也未确认视频对照标本属于六号车。",
    },
    {
        "key": "curved-frame", "label": "视频复原案例：弯曲木材制作框角",
        "start": 1914, "end": 1965, "transcription": "video_frame",
        "locator": "31:54—32:45，选取天然弯曲枝材、锯切、加工并展示框角",
        "quote": "画面观察：复原者选择弯曲木材，加工后展示用于车舆框架的弯角构件。",
        "value": "片中复原者利用天然弯曲木材加工车舆框角；这是该次现代复原采用的制作方法。",
        "types": ["type:body"],
    },
    {
        "key": "body-assembly", "label": "视频复原案例：车辀与车舆框架装配",
        "start": 1969, "end": 1988, "transcription": "video_frame",
        "locator": "32:49—33:08，带轮结构已在支架上，复原者放置车辀、车舆木框",
        "quote": "画面观察：轮组已在支架上，复原者放置车辀及车舆框架；字幕提到车舆居于车轴上方。",
        "value": "片中展示已装轮组条件下放置车辀和车舆框架，并说明舆体相对轴的位置；画面未充分展示接触面与紧固细节。",
        "types": ["type:pole", "type:body", "type:002"],
    },
    {
        "key": "woven-floor", "label": "视频复原案例：藤条编织车底",
        "start": 2091, "end": 2110, "transcription": "video_subtitle",
        "locator": "34:51—35:10，木框内编织车底，34:55字幕说明所选材料",
        "quote": "34:55英文字幕：The base of the floor will be woven rattan. 画面显示木框内的编织操作。",
        "value": "片中现代复原方案采用藤条编织车底；材料名称来自字幕说明，不能据此认定六号车的舆底材料或形制。",
        "types": ["type:body-floor"],
    },
    {
        "key": "hub-reinforcement", "label": "视频复原解释：毂端铜件的加固作用",
        "start": 2148, "end": 2149, "transcription": "video_subtitle",
        "locator": "35:48关键帧，复原者指示毂端铜件并解释其作用",
        "quote": "35:48英文字幕：It's stopping the end of the hub from splitting.",
        "value": "片中复原者解释，毂端铜件用于防止毂端开裂；这是片中构件功能的解释。",
        "types": ["type:003"], "origin": "inferred",
        "rationale": "依据复原者对构件功能的解释；本次未做力学验证。英文hub对应毂，中文字幕出现“轮轴”，因此保留英文定位并纠正实体归类。",
    },
]


def build():
    base = read_json(ROOT / "data/candidates/teacher-pdf.v0.9.json")
    data = copy.deepcopy(base)
    data.update(schema_version="0.3.0", dataset_id="dataset:knowledge-010",
                description="继承队友v0.9，补入有时间段、来源类型及适用范围的现代复原视频知识；审核状态与推断性质分别保存。")
    data["sources"].append({
        "id": "source:video1", "title": "战车视频1（用户提供，含现代复原实验与解释）",
        "resource_id": "res:video1", "filename": "战车视频1.mp4", "format": "mp4",
        "duration_seconds": 3211.56, "content_sha256": VIDEO_SHA256,
        "source_type": "modern_reconstruction_video",
        "note": "原始节目题名、制作信息及视频内各对照标本身份尚未独立核实。本文件无音轨，含烧录中英字幕；按重点关键帧核对，未逐帧审阅整片。"
                "视频中的复原对象没有被确认属于九连墩六号车。字幕存在将hub误译为轮轴的情况。",
    })
    extraction = {"method": "manual_video_frame_and_subtitle_review", "run_id": "run:20261123-video1"}
    for case in CASES:
        key = case["key"]
        record_id, evidence_id = f"record:video1-{key}", f"evidence:video1-{key}"
        scope = "适用范围仅为片中复原案例或复原者解释；不是六号车确定属性，也不自动推广为所有古代战车的通例。"
        if key == "body-assembly":
            scope += "镜头剪辑不构成完整装配顺序证据；未确认伏兔与舆底的具体接触、连接。"
        if key == "tenon-explanation":
            scope += "长短榫差异与单根辐条的股、骹分区不是同一概念。"
        data["entities"].append({"id": record_id, "kind": "ReferenceRecord", "label": case["label"],
                                 "aliases": [], "note": scope})
        data["evidence"].append({
            "id": evidence_id, "source_id": "source:video1", "start_seconds": case["start"],
            "end_seconds": case["end"], "locator": case["locator"], "quote": case["quote"],
            "transcription": case["transcription"], "check_status": "source_checked", "scope_note": scope,
        })
        origin = case.get("origin", "documented")
        description = {"id": f"fact:video1-{key}-description", "subject_id": record_id,
                       "predicate": "DESCRIPTION", "value": case["value"], "evidence_ids": [evidence_id],
                       "origin": origin, "review_status": "pending", "extraction": copy.deepcopy(extraction),
                       "knowledge_basis": "modern_reconstruction_observation" if origin == "documented" else "modern_reconstruction_inference"}
        if "rationale" in case:
            description["rationale"] = case["rationale"]
        data["facts"].append(description)
        for index, type_id in enumerate(case["types"], 1):
            data["facts"].append({"id": f"fact:video1-{key}-type-{index}", "subject_id": record_id,
                                  "predicate": "REFERS_TO_TYPE", "object_id": type_id,
                                  "evidence_ids": [evidence_id], "origin": "documented", "review_status": "pending",
                                  "knowledge_basis": "modern_reconstruction_observation", "extraction": copy.deepcopy(extraction)})
    errors = validate(data, read_json(ONTOLOGY))
    if errors:
        raise ValueError("\n".join(errors))
    summary = {"dataset_id": data["dataset_id"], "baseline": base["dataset_id"],
               "source_sha256": VIDEO_SHA256, "added": {key: len(data[key]) - len(base[key]) for key in TABLES},
               "totals": {key: len(data[key]) for key in TABLES}, "formal_confirmations": 0,
               "review_scope": "重点抽帧与字幕核对；复原推测可入库，保留其性质和范围，不要求确定无疑。"}
    return data, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, help="可选：核对本地原视频的SHA256；回放数据生成无需原视频")
    args = parser.parse_args()
    if args.video:
        with args.video.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != VIDEO_SHA256:
                raise ValueError("原视频SHA256不符，不能复用旧时间段")
    data, summary = build()
    write_json(OUTPUT, data)
    write_json(ROOT / "data/run-summaries/2026-11-23-video1-v010.json", summary)
    media = read_json(ROOT / "data/sources/fusion-media.v0.9.json")
    media["dataset_id"] = data["dataset_id"]
    write_json(ROOT / "data/sources/fusion-media.v0.10.json", media)
    print(summary)


if __name__ == "__main__":
    main()
