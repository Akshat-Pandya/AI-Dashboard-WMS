import { getComponent } from "../registry/componentRegistry";

export default function Renderer({ components = [], data = {} }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {components.map((name, index) => {
        const Component = getComponent(name);

        if (!Component) {
          return <p key={index}>Unknown component: {name}</p>;
        }

        return <Component key={index} data={data[name]} />;
      })}
    </div>
  );
}
