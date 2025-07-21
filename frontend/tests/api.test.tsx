import { emailsAPI } from "../src/services/api";
import axios from "axios";
import { expect, jest, test } from "@jest/globals";

jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

test("emailsAPI.getEmails returns data", async () => {
  mockedAxios.get.mockResolvedValue({ data: [{ id: 1 }] });
  const data = await emailsAPI.getEmails("sid", 1);
  expect(data[0].id).toBe(1);
});