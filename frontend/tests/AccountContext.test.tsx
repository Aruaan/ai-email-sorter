import React from "react";
import { render, screen } from "@testing-library/react";
import { AccountProvider, useAccount } from "../src/contexts/AccountContext";
import { expect, test } from "@jest/globals";

function TestComponent() {
  const { activeAccount, setActiveAccount } = useAccount();
  return (
    <div>
      <span data-testid="active">{activeAccount}</span>
      <button onClick={() => setActiveAccount("new@example.com")}>Set</button>
    </div>
  );
}

test("AccountProvider initializes and updates activeAccount", () => {
  render(
    <AccountProvider initialActiveAccount="init@example.com">
      <TestComponent />
    </AccountProvider>
  );
  expect(screen.getByTestId("active").textContent).toBe("init@example.com");
  screen.getByText("Set").click();
  expect(screen.getByTestId("active").textContent).toBe("new@example.com");
});
