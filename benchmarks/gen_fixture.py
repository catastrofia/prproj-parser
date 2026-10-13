"""Generate synthetic .prproj files that mirror real Premiere Pro structure.

Used for benchmarking the parser at scale without committing private
project files. Structure follows docs/prproj-format/ and tests/conftest.py.

Usage: python gen_fixture.py <n_clips_per_track> <n_seqs> <out_path.prproj>
"""

import gzip
import sys

HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n<PremiereData Version="3">\n'
FOOTER = "</PremiereData>\n"


def generate(n_clips_per_track: int, n_seqs: int, media_pool: int) -> str:
    parts = [HEADER]
    vc_id = 1000  # VideoClip / VideoMediaSource id space
    item_id = 100000  # TrackItem id space
    sub_id = 500000  # SubClip id space
    junk_id = 900000  # junk element id space

    # Shared media pool: M media / masterclips reused by all clips
    for m in range(media_pool):
        vc_id += 1
        parts.append(
            f'  <VideoClip ObjectID="{vc_id}" ClassID="vc" Version="1">\n'
            f'    <Clip Version="1"><Source ObjectRef="{vc_id + media_pool}"/>'
            f"<PlaybackSpeed>1.0</PlaybackSpeed></Clip>\n  </VideoClip>\n"
        )
        parts.append(
            f'  <VideoMediaSource ObjectID="{vc_id + media_pool}" ClassID="vms" Version="1">\n'
            f'    <Media ObjectURef="media-uid-{m:06d}"/>\n  </VideoMediaSource>\n'
        )
        parts.append(
            f'  <Media ObjectUID="media-uid-{m:06d}" ClassID="m" Version="28">\n'
            f"    <FilePath>C:\\\\Media\\\\clip_{m:06d}.mp4</FilePath>\n"
            f"    <Title>clip_{m:06d}.mp4</Title>\n"
            f"    <ActualMediaFilePath>C:\\\\Media\\\\clip_{m:06d}.mp4</ActualMediaFilePath>\n"
            f"  </Media>\n"
        )
        parts.append(
            f'  <MasterClip ObjectUID="mc-uid-{m:06d}" ClassID="mc" Version="11">\n'
            f"    <Name>clip_{m:06d}.mp4</Name>\n"
            f'    <Clips Version="1"><Clip ObjectRef="{1001 + m}"/></Clips>\n'
            f"  </MasterClip>\n"
        )

    # Object definitions are emitted flat (siblings of <PremiereData>),
    # collected here while tracks reference them, written at the end.
    defs = []

    for s in range(n_seqs):
        parts.append(
            f'  <Sequence ObjectUID="seq-uid-{s:04d}" ClassID="seq" Version="11">\n'
            f'    <TrackGroups Version="1">\n'
            f'      <TrackGroup Version="1" Index="0"><Second ObjectRef="{700000 + s * 2}"/></TrackGroup>\n'
            f'      <TrackGroup Version="1" Index="1"><Second ObjectRef="{700001 + s * 2}"/></TrackGroup>\n'
            f"    </TrackGroups>\n"
            f"    <Name>Sequence {s:03d}</Name>\n  </Sequence>\n"
        )
        # Track groups (video id 700000+2s, audio 700001+2s)
        for kind, tid in (("Video", 700000 + s * 2), ("Audio", 700001 + s * 2)):
            parts.append(
                f'  <{kind}TrackGroup ObjectID="{tid}" ClassID="tg" Version="13">\n'
                f'    <TrackGroup Version="1">\n'
                f'      <Tracks Version="1"><Track Index="0" ObjectURef="trk-uid-{s:04d}-{kind[0]}"/></Tracks>\n'
                f"      <FrameRate>10160640000</FrameRate>\n"
                f"    </TrackGroup>\n  </{kind}TrackGroup>\n"
            )
        # Tracks + items
        for kind in ("Video", "Audio"):
            parts.append(
                f'  <{kind}ClipTrack ObjectUID="trk-uid-{s:04d}-{kind[0]}" ClassID="ct" Version="11">\n'
                f'    <ClipTrack Version="2">\n'
                f'      <Track Version="3"><Index>0</Index></Track>\n'
                f'      <ClipItems Version="3">\n        <TrackItems Version="1">\n'
            )
            for c in range(n_clips_per_track):
                item_id += 1
                sub_id += 1
                item = item_id
                mc = (item_id + c + s) % media_pool
                start = c * 254016000000
                end = start + 200000000000
                parts.append(f'          <TrackItem Index="{c}" ObjectRef="{item}"/>\n')
                defs.append(
                    f'  <{kind}ClipTrackItem ObjectID="{item}" ClassID="ti" Version="6">\n'
                    f'    <ClipTrackItem Version="8">\n'
                    f'      <TrackItem Version="3"><Start>{start}</Start><End>{end}</End></TrackItem>\n'
                    f'      <SubClip ObjectRef="{sub_id}"/>\n'
                    f"    </ClipTrackItem>\n  </{kind}ClipTrackItem>\n"
                )
                defs.append(
                    f'  <SubClip ObjectID="{sub_id}" ClassID="sc" Version="5">\n'
                    f'    <MasterClip ObjectURef="mc-uid-{mc:06d}"/>\n'
                    f"    <Name>clip_{mc:06d}.mp4</Name>\n  </SubClip>\n"
                )
                # junk elements interleaved (as in real files)
                junk_id += 2
            parts.append(
                "        </TrackItems>\n      </ClipItems>\n    </ClipTrack>\n"
                f"  </{kind}ClipTrack>\n"
            )

    parts.extend(defs)
    # Interleave junk elements at depth 2 (flat siblings, as in real files)
    n_junk = (junk_id - 900000) // 2
    for j in range(n_junk):
        parts.append(
            f'  <VideoComponentParam ObjectID="{900000 + j * 2}" ClassID="t" Version="1">'
            f"<Name>Opacity</Name></VideoComponentParam>\n"
            f'  <VideoFilterComponent ObjectID="{900001 + j * 2}" ClassID="t" Version="1">'
            f"<Name>Motion</Name></VideoFilterComponent>\n"
        )

    parts.append(FOOTER)
    return "".join(parts)


def main() -> None:
    n_clips = int(sys.argv[1])
    n_seqs = int(sys.argv[2])
    out = sys.argv[3]
    xml = generate(n_clips, n_seqs, media_pool=max(20, n_clips // 5))
    data = xml.encode("utf-8")
    if out.endswith(".gz") or out.endswith(".prproj"):
        with gzip.open(out, "wb", compresslevel=6) as f:
            f.write(data)
    else:
        with open(out, "wb") as f:
            f.write(data)
    print(f"{out}: {len(data) / 1e6:.1f} MB XML uncompressed")


if __name__ == "__main__":
    main()
