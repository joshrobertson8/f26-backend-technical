export interface User {
  id: string;
  name: string;
}

export interface EventInput {
  title: string;
  description: string;
  inviteeIds: string[];
}

export interface Event extends EventInput {
  id: string;
}
