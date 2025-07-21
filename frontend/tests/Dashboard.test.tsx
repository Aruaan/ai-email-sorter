import { render, screen, waitFor } from "@testing-library/react";
import Dashboard from "../src/pages/Dashboard";
import * as api from "../src/services/api";
import { expect, jest, test } from "@jest/globals";
import React from "react";
import "@testing-library/jest-dom";

jest.mock("../src/services/api");



test("loads categories and displays them", async () => {
  jest.spyOn(api.categoriesAPI, "getCategories").mockResolvedValue([{ id: "1", name: "Cat1", session_id: "s" }]);
  render(<Dashboard userEmail="u" sessionId="s" sessionInfo={null} onLogout={() => {}} onSessionUpdate={() => {}} />);
  expect(await screen.findByText("Cat1")).toBeTruthy();
});
