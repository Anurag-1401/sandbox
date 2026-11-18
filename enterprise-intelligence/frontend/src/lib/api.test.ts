
import { describe, expect, it } from "vitest";
import type { AxiosError } from "axios";

import { getApiErrorMessage } from "./api";

function fakeAxiosError(
  status: number,
  detail?: unknown
): AxiosError {
  return {
    isAxiosError: true,
    message: "Request failed",
    name: "AxiosError",
    config: { headers: {} } as AxiosError["config"],
    response: {
      status,
      statusText: "",
      headers: {},
      config: { headers: {} } as AxiosError["config"],
      data: detail === undefined ? {} : { detail }
    }
  } as AxiosError;
}

describe("getApiErrorMessage", () => {
  it("returns a backend detail string", () => {
    const error = fakeAxiosError(400, "Invalid request");

    expect(getApiErrorMessage(error)).toBe("Invalid request");
  });

  it("handles forbidden responses", () => {
    const error = fakeAxiosError(403);

    expect(getApiErrorMessage(error)).toContain("permission");
  });

  it("formats FastAPI validation errors", () => {
    const error = fakeAxiosError(422, [
      {
        loc: ["body", "title"],
        msg: "Field required",
        type: "missing"
      }
    ]);

    expect(getApiErrorMessage(error)).toContain(
      "title: Field required"
    );
  });

  it("handles server errors", () => {
    const error = fakeAxiosError(500);

    expect(getApiErrorMessage(error)).toContain("server");
  });
});
