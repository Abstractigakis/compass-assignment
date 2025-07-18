import React from "react";

type Props = {
  json: object | null;
};

const PrettyJson = ({ json }: Props) => {
  if (!json) return null;
  return <pre>{JSON.stringify(json, null, 2)}</pre>;
};

export default PrettyJson;
