import { Audio } from "@remotion/media";
import React from "react";
import { AbsoluteFill, Sequence, staticFile, useVideoConfig } from "remotion";
import {
  DistanceScene,
  EndScene,
  GraveyardScene,
  HookScene,
  IssScene,
  NemoScene,
} from "./scenes";
import { Captions, Ocean, Progress } from "./ui";

// Los inicios de escena (en frames a 30 fps) salen de timings.json, generado por nemo/tts.py.
export const PuntoNemo: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#02070f" }}>
      <Ocean />
      <Sequence name="Gancho" from={0} durationInFrames={176}>
        <HookScene />
      </Sequence>
      <Sequence name="Punto Nemo" from={176} durationInFrames={160}>
        <NemoScene />
      </Sequence>
      <Sequence name="Distancia" from={336} durationInFrames={173}>
        <DistanceScene />
      </Sequence>
      <Sequence name="Estación espacial" from={509} durationInFrames={232}>
        <IssScene />
      </Sequence>
      <Sequence name="Cementerio" from={741} durationInFrames={237}>
        <GraveyardScene />
      </Sequence>
      <Sequence name="Final" from={978} durationInFrames={267}>
        <EndScene />
      </Sequence>
      <Captions />
      <Progress />

      <Audio name="Voz" src={staticFile("nemo/voz.wav")} />
      <Audio name="Ambiente" src={staticFile("nemo/ambiente.wav")} volume={0.35} />
      <Sequence name="SFX ping" from={176} durationInFrames={2 * fps}>
        <Audio src={staticFile("nemo/ping.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX boom gancho" from={123} durationInFrames={2 * fps}>
        <Audio src={staticFile("nemo/boom.wav")} volume={0.6} />
      </Sequence>
      <Sequence name="SFX whoosh 1" from={334} durationInFrames={fps}>
        <Audio src={staticFile("nemo/whoosh.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX whoosh 2" from={507} durationInFrames={fps}>
        <Audio src={staticFile("nemo/whoosh.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX whoosh 3" from={739} durationInFrames={fps}>
        <Audio src={staticFile("nemo/whoosh.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX boom final" from={1103} durationInFrames={2 * fps}>
        <Audio src={staticFile("nemo/boom.wav")} volume={0.8} />
      </Sequence>
    </AbsoluteFill>
  );
};
