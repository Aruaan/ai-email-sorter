import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import CategoryView from "../src/pages/CategoryView";
import * as api from "../src/services/api"
import { expect, jest, test } from "@jest/globals";

jest.mock("../src/services/api");

test("loads emails and displays them", async () => {
  (api.emailsAPI.getEmails as jest.MockedFunction<typeof api.emailsAPI.getEmails>).mockResolvedValue([
    { id: "1", subject: "Subj", from_email: "f", category_id: "1", summary: "s", raw: "r", user_email: "u", gmail_id: "g" }
  ]);
  render(<CategoryView sessionId="s" sessionInfo={null} userEmail="u" />);
  await waitFor(() => {
    expect(screen.getByText("Subj")).toBeTruthy();
  });
});
