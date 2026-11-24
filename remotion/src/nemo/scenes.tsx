import React from "react";
import {
  AbsoluteFill,
  Easing,
  Interactive,
  interpolate,
  random,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ACCENT, CYAN, Counter, bodyFont, titleFont } from "./ui";

/** Estación espacial dibujada en SVG. */
const Station: React.FC<{ size: number; glow?: string }> = ({
  size,
  glow = CYAN,
}) => (
  <svg
    width={size}
    height={size * 0.5}
    viewBox="0 0 200 100"
    style={{ filter: `drop-shadow(0 0 18px ${glow})` }}
  >
    <rect x="10" y="47" width="180" height="6" fill="#d9e2ec" />
    {[14, 46, 130, 162].map((x) => (
      <React.Fragment key={x}>
        <rect x={x} y="8" width="24" height="36" fill="#2c6fb8" stroke="#9ecbff" strokeWidth="1.5" />
        <rect x={x} y="56" width="24" height="36" fill="#2c6fb8" stroke="#9ecbff" strokeWidth="1.5" />
      </React.Fragment>
    ))}
    <rect x="84" y="38" width="32" height="24" rx="4" fill="#f1f5f9" />
    <rect x="94" y="30" width="12" height="40" rx="3" fill="#cbd5e1" />
  </svg>
);

/** Punto pulsante amarillo: el Punto Nemo. */
const NemoDot: React.FC<{ x: number; y: number }> = ({ x, y }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ position: "absolute", left: x, top: y }}>
      {[0, 20, 40].map((d) => {
        const p = ((frame + d) % 60) / 60;
        return (
          <div
            key={d}
            style={{
              position: "absolute",
              width: 40,
              height: 40,
              left: -20,
              top: -20,
              borderRadius: "50%",
              border: `4px solid ${ACCENT}`,
              opacity: 1 - p,
              scale: String(1 + p * 5),
            }}
          />
        );
      })}
      <div
        style={{
          position: "absolute",
          width: 34,
          height: 34,
          left: -17,
          top: -17,
          borderRadius: "50%",
          background: ACCENT,
          boxShadow: `0 0 40px ${ACCENT}`,
        }}
      />
    </div>
  );
};

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

// ───────────────────────── 1. GANCHO ─────────────────────────
export const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Interactive.Div
        name="Titular gancho"
        style={{
          position: "absolute",
          top: 150,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: titleFont,
          fontSize: 120,
          lineHeight: 1.02,
          color: "white",
          textTransform: "uppercase",
          scale: interpolate(frame, [0, 10], [1.6, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          }),
          opacity: interpolate(frame, [0, 6, 128, 142], [0, 1, 1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        El lugar más <span style={{ color: ACCENT }}>solitario</span> del planeta
      </Interactive.Div>
      <NemoDot x={540} y={1060} />
      {/* línea que sube hacia el espacio */}
      <div
        style={{
          position: "absolute",
          left: 537,
          bottom: 1920 - 1040,
          width: 6,
          height: interpolate(frame, [75, 142], [0, 640], {
            ...clamp,
            easing: Easing.inOut(Easing.cubic),
          }),
          background: `repeating-linear-gradient(to top, ${CYAN} 0 18px, transparent 18px 32px)`,
        }}
      />
      <Interactive.Div
        name="Estación en el gancho"
        style={{
          position: "absolute",
          left: 340,
          top: 270,
          opacity: interpolate(frame, [140, 148], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          scale: interpolate(frame, [140, 153], [0.3, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(2.5)),
            output: "perceptual-scale",
          }),
        }}
      >
        <Station size={400} />
      </Interactive.Div>
    </AbsoluteFill>
  );
};

// ───────────────────────── 2. PUNTO NEMO ─────────────────────────
export const NemoScene: React.FC = () => {
  const frame = useCurrentFrame();
  const coords = "48°52′S · 123°23′O";
  const typed = coords.slice(
    0,
    Math.round(interpolate(frame, [20, 60], [0, coords.length], clamp)),
  );
  return (
    <AbsoluteFill>
      {/* retícula */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1000,
          height: 2,
          background: CYAN,
          opacity: 0.35,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 0,
          bottom: 0,
          left: 539,
          width: 2,
          background: CYAN,
          opacity: 0.35,
        }}
      />
      <NemoDot x={540} y={1000} />
      <Interactive.Div
        name="Título Punto Nemo"
        style={{
          position: "absolute",
          top: 260,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: titleFont,
          fontSize: 190,
          color: ACCENT,
          letterSpacing: interpolate(frame, [0, 25], ["40px", "4px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          }),
          opacity: interpolate(frame, [0, 8], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          textShadow: "0 0 50px rgba(255,212,0,.45)",
        }}
      >
        PUNTO NEMO
      </Interactive.Div>
      <div
        style={{
          position: "absolute",
          top: 500,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: "monospace",
          fontSize: 56,
          color: CYAN,
        }}
      >
        {typed}
      </div>
      <Interactive.Div
        name="Nemo significa nadie"
        style={{
          position: "absolute",
          top: 610,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: bodyFont,
          fontWeight: 800,
          fontSize: 46,
          color: "white",
          opacity: interpolate(frame, [70, 85], [0, 0.85], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        «Nemo» = «nadie» en latín
      </Interactive.Div>
    </AbsoluteFill>
  );
};

// ───────────────────────── 3. DISTANCIA ─────────────────────────
const ISLANDS = [
  { name: "ISLA DUCIE", angle: -35 },
  { name: "MOTU NUI", angle: 75 },
  { name: "ISLA MAHER", angle: 200 },
];

export const DistanceScene: React.FC = () => {
  const frame = useCurrentFrame();
  const r = interpolate(frame, [10, 70], [0, 320], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const cx = 540;
  const cy = 900;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: cx - r,
          top: cy - r,
          width: r * 2,
          height: r * 2,
          borderRadius: "50%",
          border: `4px dashed ${CYAN}`,
          opacity: 0.8,
        }}
      />
      <NemoDot x={cx} y={cy} />
      {ISLANDS.map((isl, i) => {
        const a = (isl.angle * Math.PI) / 180;
        const appear = interpolate(frame, [70 + i * 8, 80 + i * 8], [0, 1], clamp);
        return (
          <div
            key={isl.name}
            style={{
              position: "absolute",
              left: cx + Math.cos(a) * 320,
              top: cy + Math.sin(a) * 320,
              opacity: appear,
            }}
          >
            <div
              style={{
                position: "absolute",
                left: -16,
                top: -16,
                width: 32,
                height: 32,
                borderRadius: 8,
                background: "#3ddc84",
                boxShadow: "0 0 25px #3ddc84",
              }}
            />
            <div
              style={{
                position: "absolute",
                left: -200,
                width: 400,
                top: 26,
                textAlign: "center",
                fontFamily: bodyFont,
                fontWeight: 800,
                fontSize: 34,
                color: "#3ddc84",
              }}
            >
              {isl.name}
            </div>
          </div>
        );
      })}
      <Counter
        to={2688}
        delay={65}
        durationInFrames={55}
        suffix=" KM"
        style={{
          position: "absolute",
          top: 230,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: titleFont,
          fontSize: 200,
          color: ACCENT,
          textShadow: "0 0 50px rgba(255,212,0,.4)",
        }}
      />
      <Interactive.Div
        name="Hasta la tierra más cercana"
        style={{
          position: "absolute",
          top: 470,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: bodyFont,
          fontWeight: 800,
          fontSize: 46,
          color: "white",
        }}
      >
        hasta la tierra más cercana
      </Interactive.Div>
    </AbsoluteFill>
  );
};

// ───────────────────────── 4. ESTACIÓN ESPACIAL ─────────────────────────
export const IssScene: React.FC = () => {
  const frame = useCurrentFrame();
  // escala real: 1 km ≈ 0,4 px → 400 km = 160 px; 2.688 km = 1.075 px (se sale de la pantalla)
  const ox = 260;
  const oy = 1150;
  const up = interpolate(frame, [15, 45], [0, 160], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const side = interpolate(frame, [60, 110], [0, 1075], {
    ...clamp,
    easing: Easing.inOut(Easing.cubic),
  });
  return (
    <AbsoluteFill>
      <NemoDot x={ox} y={oy} />
      <div
        style={{
          position: "absolute",
          left: ox - 3,
          top: oy - up,
          width: 6,
          height: up,
          background: CYAN,
        }}
      />
      <div style={{ position: "absolute", left: ox - 130, top: oy - up - 130 }}>
        <Station size={260} />
      </div>
      <div
        style={{
          position: "absolute",
          left: ox + 40,
          top: oy - 120,
          fontFamily: titleFont,
          fontSize: 80,
          color: CYAN,
          opacity: interpolate(frame, [40, 50], [0, 1], clamp),
        }}
      >
        400 KM ↑
      </div>
      <div
        style={{
          position: "absolute",
          left: ox,
          top: oy + 40,
          width: side,
          height: 6,
          background: "#3ddc84",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: ox + 40,
          top: oy + 70,
          fontFamily: titleFont,
          fontSize: 80,
          color: "#3ddc84",
          opacity: interpolate(frame, [90, 100], [0, 1], clamp),
        }}
      >
        2.688 KM →
      </div>
      <Interactive.Div
        name="Astronautas más cerca"
        style={{
          position: "absolute",
          top: 230,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: titleFont,
          fontSize: 116,
          lineHeight: 1.05,
          color: "white",
          opacity: interpolate(frame, [105, 115], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          scale: interpolate(frame, [105, 120], [0.6, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(2)),
            output: "perceptual-scale",
          }),
        }}
      >
        Los astronautas están <span style={{ color: ACCENT }}>casi 7 veces</span> más cerca
      </Interactive.Div>
    </AbsoluteFill>
  );
};

// ───────────────────────── 5. CEMENTERIO DE NAVES ─────────────────────────
export const GraveyardScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const items = new Array(14).fill(0).map((_, i) => ({
    x: 120 + random(`x${i}`) * 840,
    start: 40 + i * 11,
    size: 50 + random(`s${i}`) * 50,
  }));
  const seaY = 1150;
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: seaY,
          bottom: 0,
          background: "linear-gradient(#0a3a63cc, #010409)",
          borderTop: `3px solid ${CYAN}`,
        }}
      />
      {items.map((it, i) => {
        const f = frame - it.start;
        if (f < 0) return null;
        const fallDur = 0.7 * fps;
        const y = interpolate(f, [0, fallDur], [-150, seaY], {
          ...clamp,
          easing: Easing.in(Easing.quad),
        });
        const splash = interpolate(f, [fallDur, fallDur + 20], [0, 1], clamp);
        return (
          <React.Fragment key={i}>
            {splash === 0 ? (
              <div
                style={{
                  position: "absolute",
                  left: it.x - it.size / 2,
                  top: y - it.size * 3,
                  width: it.size,
                  height: it.size * 3,
                  background: `linear-gradient(transparent, #ff7a1a)`,
                  borderRadius: it.size,
                  filter: "blur(4px)",
                }}
              />
            ) : null}
            {splash === 0 ? (
              <div
                style={{
                  position: "absolute",
                  left: it.x - it.size / 2,
                  top: y - it.size / 2,
                  width: it.size,
                  height: it.size,
                  borderRadius: "30%",
                  background: "#e2e8f0",
                  boxShadow: "0 0 30px #ffb347",
                }}
              />
            ) : (
              <div
                style={{
                  position: "absolute",
                  left: it.x - 60,
                  top: seaY - 15,
                  width: 120,
                  height: 30,
                  borderRadius: "50%",
                  border: `3px solid ${CYAN}`,
                  opacity: 1 - splash,
                  scale: String(0.5 + splash * 1.5),
                }}
              />
            )}
            {/* restos en el fondo */}
            {splash > 0 ? (
              <div
                style={{
                  position: "absolute",
                  left: it.x - 12,
                  top: seaY + 470 + random(`d${i}`) * 220,
                  width: 24,
                  height: 14,
                  background: "#64748b",
                  opacity: splash * 0.8,
                  rotate: `${random(`r${i}`) * 90}deg`,
                }}
              />
            ) : null}
          </React.Fragment>
        );
      })}
      <Counter
        to={260}
        delay={145}
        durationInFrames={45}
        suffix=""
        style={{
          position: "absolute",
          top: 200,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: titleFont,
          fontSize: 230,
          color: ACCENT,
          textShadow: "0 0 50px rgba(255,212,0,.4)",
        }}
      />
      <Interactive.Div
        name="Naves hundidas"
        style={{
          position: "absolute",
          top: 480,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: bodyFont,
          fontWeight: 900,
          fontSize: 52,
          color: "white",
        }}
      >
        NAVES ESPACIALES HUNDIDAS
      </Interactive.Div>
      <Interactive.Div
        name="Etiqueta Mir"
        style={{
          position: "absolute",
          top: 600,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: "monospace",
          fontSize: 44,
          color: CYAN,
          opacity: interpolate(frame, [175, 190], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        incluida la estación MIR (2001)
      </Interactive.Div>
    </AbsoluteFill>
  );
};

// ───────────────────────── 6. FINAL ─────────────────────────
export const EndScene: React.FC = () => {
  const frame = useCurrentFrame();
  const seaY = 1150;
  const issY = interpolate(frame, [0, 125], [120, seaY - 100], {
    ...clamp,
    easing: Easing.in(Easing.cubic),
  });
  const impact = interpolate(frame, [125, 150], [0, 1], clamp);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: seaY,
          bottom: 0,
          background: "linear-gradient(#0a3a63cc, #010409)",
          borderTop: `3px solid ${CYAN}`,
        }}
      />
      {impact === 0 ? (
        <div
          style={{
            position: "absolute",
            left: 330,
            top: issY,
            rotate: `${interpolate(frame, [0, 125], [0, 25], clamp)}deg`,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 150,
              top: -420,
              width: 120,
              height: 460,
              background: "linear-gradient(transparent, #ff7a1a)",
              borderRadius: 60,
              filter: "blur(10px)",
              opacity: interpolate(frame, [20, 80], [0, 1], clamp),
            }}
          />
          <Station size={420} glow="#ff7a1a" />
        </div>
      ) : (
        <div
          style={{
            position: "absolute",
            left: 540 - 300,
            top: seaY - 300,
            width: 600,
            height: 600,
            borderRadius: "50%",
            background: "radial-gradient(#fff6, #ff7a1a55 40%, transparent 70%)",
            opacity: 1 - impact,
            scale: String(0.4 + impact),
          }}
        />
      )}
      <Interactive.Div
        name="Año 2030"
        style={{
          position: "absolute",
          top: 200,
          left: 0,
          right: 0,
          textAlign: "center",
          fontFamily: titleFont,
          fontSize: 220,
          color: ACCENT,
          textShadow: "0 0 50px rgba(255,212,0,.4)",
          opacity: interpolate(frame, [0, 10, 140, 150], [0, 1, 1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        2030
      </Interactive.Div>
      <Interactive.Div
        name="Botón sígueme"
        style={{
          position: "absolute",
          top: 420,
          left: 190,
          width: 700,
          padding: "36px 0",
          borderRadius: 999,
          background: ACCENT,
          color: "#06101c",
          textAlign: "center",
          fontFamily: titleFont,
          fontSize: 110,
          boxShadow: "0 0 60px rgba(255,212,0,.6)",
          opacity: interpolate(frame, [175, 183], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          scale: interpolate(frame, [175, 190], [0.4, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(3)),
            output: "perceptual-scale",
          }),
        }}
      >
        SÍGUEME
      </Interactive.Div>
    </AbsoluteFill>
  );
};
