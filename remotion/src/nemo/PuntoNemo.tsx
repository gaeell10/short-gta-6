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
      <Sequence name="Punto Nemo" from={176} durationInFrames={176}>
        <NemoScene />
      </Sequence>
      <Sequence name="Distancia" from={352} durationInFrames={172}>
        <DistanceScene />
      </Sequence>
      <Sequence name="Estación espacial" from={524} durationInFrames={212}>
        <IssScene />
      </Sequence>
      <Sequence name="Cementerio" from={736} durationInFrames={237}>
        <GraveyardScene />
      </Sequence>
      <Sequence name="Final" from={973} durationInFrames={277}>
        <EndScene />
      </Sequence>
      <Captions />
      <Progress />

      <Audio name="Voz" src={staticFile("nemo/voz.wav")} />
      <Audio name="Ambiente" src={staticFile("nemo/ambiente.wav")} volume={0.35} />
      <Sequence name="SFX ping" from={176} durationInFrames={2 * fps}>
        <Audio src={staticFile("nemo/ping.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX boom gancho" from={142} durationInFrames={2 * fps}>
        <Audio src={staticFile("nemo/boom.wav")} volume={0.6} />
      </Sequence>
      <Sequence name="SFX whoosh 1" from={350} durationInFrames={fps}>
        <Audio src={staticFile("nemo/whoosh.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX whoosh 2" from={522} durationInFrames={fps}>
        <Audio src={staticFile("nemo/whoosh.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX whoosh 3" from={734} durationInFrames={fps}>
        <Audio src={staticFile("nemo/whoosh.wav")} volume={0.5} />
      </Sequence>
      <Sequence name="SFX boom final" from={1098} durationInFrames={2 * fps}>
        <Audio src={staticFile("nemo/boom.wav")} volume={0.8} />
      </Sequence>
    </AbsoluteFill>
  );
};
