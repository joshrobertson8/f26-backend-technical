import { createApp } from "./app";

const app = createApp();
const port = Number(process.env.PORT || 8000);

app.listen(port, "127.0.0.1", () => {
  console.log(`Event API: http://127.0.0.1:${port}/api`);
});
