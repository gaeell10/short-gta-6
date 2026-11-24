import { Composition } from "remotion";
import { MyComposition } from "./Composition";
import { PuntoNemo } from "./nemo/PuntoNemo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <MyComposition />
      <Composition
        id="PuntoNemo"
        component={PuntoNemo}
        durationInFrames={1245}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
