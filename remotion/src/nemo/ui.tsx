import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import timings from "./timings.json";

export const { fontFamily: titleFont } = loadAnton("normal", {
  weights: ["400"],
  subsets: ["latin"],
});
export const { fontFamily: bodyFont } = loadInter("normal", {
  weights: ["800", "900"],
  subsets: ["latin"],
});

export const ACCENT = "#ffd400";
export const CYAN = "#5ee7ff";

/** Fondo de océano nocturno con olas animadas. */
export const Ocean: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const waves = [0, 1, 2, 3, 4, 5, 6, 7];
  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(120% 70% at 50% 45%, #0b2a4a 0%, #061a30 45%, #02070f 100%)",
      }}
    >
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {waves.map((i) => {
          const y = 620 + i * 150;
          const amp = 14 + i * 3;
          const phase = frame * (0.03 + i * 0.004) + i;
          let d = `M 0 ${y}`;
          for (let x = 0; x <= width; x += 30) {
            d += ` L ${x} ${y + Math.sin(x / 140 + phase) * amp}`;
          }
          return (
            <path
              key={i}
              d={d}
              fill="none"
              stroke={CYAN}
              strokeOpacity={0.05 + i * 0.012}
              strokeWidth={2}
            />
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

/** Barra de progreso arriba: ayuda a la retención. */
export const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        height: 10,
        width: `${(frame / durationInFrames) * 100}%`,
        background: ACCENT,
        boxShadow: `0 0 20px ${ACCENT}`,
      }}
    />
  );
};

const KEYWORDS = [
  "espacio",
  "nemo",
  "alejado",
  "pacífico",
  "seiscientos",
  "kilómetros",
  "cuatrocientos",
  "astronautas",
  "mejor",
  "oye",
  "satélites",
  "doscientas",
  "naves",
  "treinta",
  "estación",
  "sígueme",
  "cabeza",
];

/**
 * Subtítulos generados a partir de timings.json (salida de nemo/tts.py).
 * Son datos generados, así que no se editan desde el Studio.
 */
export const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const lines = timings.scenes.flatMap((s) => s.lines);
  const line = lines.find((l) => t >= l.start && t < l.end + 0.25);
  if (!line) return null;
  const words = line.text.split(" ");
  const totalChars = line.text.length;
  let acc = 0;
  const lineFrame = (t - line.start) * fps;
  return (
    <div
      style={{
        position: "absolute",
        left: 80,
        right: 80,
        bottom: 330,
        textAlign: "center",
        fontFamily: bodyFont,
        fontWeight: 900,
        fontSize: 68,
        lineHeight: 1.18,
        color: "white",
        textTransform: "uppercase",
        textShadow: "0 6px 0 #000, 0 0 30px rgba(0,0,0,.9)",
        scale: interpolate(lineFrame, [0, 6], [0.9, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.out(Easing.back(2)),
        }),
      }}
    >
      {words.map((w, i) => {
        const wStart =
          line.start + (acc / totalChars) * (line.end - line.start);
        acc += w.length + 1;
        const visible = t >= wStart - 0.05;
        const clean = w
          .toLowerCase()
          .replace(/[.,¿?¡!]/g, "");
        const hot = KEYWORDS.includes(clean);
        return (
          <span
            key={i}
            style={{
              opacity: visible ? 1 : 0.18,
              color: hot ? ACCENT : "white",
              marginRight: 18,
              display: "inline-block",
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};

/** Contador numérico animado. */
export const Counter: React.FC<{
  to: number;
  delay?: number;
  durationInFrames: number;
  suffix: string;
  style?: React.CSSProperties;
}> = ({ to, delay = 0, durationInFrames, suffix, style }) => {
  const frame = useCurrentFrame();
  const v = interpolate(frame, [delay, delay + durationInFrames], [0, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  return (
    <div style={style}>
      {String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, ".")}
      {suffix}
    </div>
  );
};
