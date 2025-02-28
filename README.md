# GraphQL Chat & Subscription API

![GraphQL](https://img.shields.io/badge/GraphQL-E10098.svg?style=for-the-badge&logo=GraphQL&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20.svg?style=for-the-badge&logo=Django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A.svg?style=for-the-badge&logo=Celery&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000.svg?style=for-the-badge&logo=JSON-Web-Tokens&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1.svg?style=for-the-badge&logo=PostgreSQL&logoColor=white)

A chat platform built with Django and GraphQL that implements a subscription-based messaging system with access limits.

## Table of Contents

- Installation
- Features
- Architecture
- Authentication System
- Testing
- GraphQL API

## Installation

```bash
# Clone the repository
git clone https://github.com/houshmand-2005/GraphQL_Task.git
cd GraphQL_Task

# Run the server
sudo docker compose up
```

The application will be available at `http://localhost:8000/graphql`.

To create superuser:

```bash
sudo docker compose exec web uv run python manage.py createsuperuser
```

## Features

- **User Authentication**: Complete JWT-based authentication system with email verification
- **Conversation Management**: Create, list, and manage conversations
- **Messaging System**: Send and retrieve messages within conversations
- **Access Controls**: Permission-based system for resource access
- **Asynchronous Processing**: Email handling and background tasks with Celery
- **Testing**: Most of the components are covered with unit tests

## Architecture

The application is built on a modular architecture divided into distinct Django apps:

- users: Handles user registration, authentication, and profile management
- subscriptions: Manages subscription plans, user subscriptions, and usage limits
- chat: Provides conversation and messaging functionality
- core: Contains project settings and configuration
- utils: Shared utility functions and services

### Data Model Overview

```
┌──────────────┐     ┌────────────────┐     ┌───────────────┐
│  CustomUser  │     │SubscriptionPlan│     │  Conversation │
├──────────────┤     ├────────────────┤     ├───────────────┤
│ user_name    │     │ name           │     │ title         │
│ email        │     │ description    │     │ owner         │◄─┐
│ password     │     │ price          │     │ members       │  │
│ is_active    │     │ max_characters │     └───────────────┘  │
│ is_staff     │     │ max_conversa-  │            │           │
│ is_active    │     │ tions          │            ▼           │
│ ...          │     │ is_active      │                        │
└──────────────┘     │ is_default     │     ┌───────────────┐  │
        ▲            └────────────────┘     │    Message    │  │
        │                                   ├───────────────┤  │
        │                     ▲             │ text          │  │
        │                     │             │ sender        │──┘
        │             ┌────────────────┐    │ conversation  │
        └─────────────┤UserSubscription│    │ created_at    │
                      ├────────────────┤    └───────────────┘
                      │ user           │
                      │ plan           │
                      └────────────────┘
```

## Authentication System

The application uses JWT (JSON Web Tokens) for authentication

### Registration Flow

1. User submits registration information via GraphQL mutation
2. System creates an inactive user account
3. Verification email is generated and queued in Celery
4. Celery worker processes the email and sends it to the user
5. Users can activate their account via verification token

## Testing

The project includes comprehensive tests for all components:

```bash
# Run all tests
python manage.py test
```

## GraphQL API

The API is built with Graphene-Django and provides a comprehensive set of queries and mutations:

### Core Mutations

#### User Mutations

```graphql
1)

mutation {
  registerUser(
    userName: "user_name"
    email: "test@test.com"
    password: "your_password"
    firstName: "Your"
    lastName: "Name"
  ) {
    user {
      id
      userName
      email
      firstName
      lastName
    }
  }
}

2)

mutation {
  verifyEmail(token: "...") {
    success
    message
  }
}

3)
mutation LoginUser {
  login(username: "user_name", password: "your_password") {
    token {
      access
      refresh
    }
    user {
      id
      userName
      email
      firstName
      lastName
    }
  }
}
```

#### Subscription Mutations

```graphql
1)

mutation CreateNewPlan {
  createSubscriptionPlan(
    name: "Premium"
    description: "Pro subscription"
    maxCharacters: 10
    maxConversations: 20
    price: 9.99
  ) {
    success
    message
    plan {
      id
      name
      description
    }
  }
}

2)

mutation UpgradeMyPlan {
  upgradeSubscription(planId: "2") {
    success
    message
    subscription {
      plan {
        name
        maxCharacters
        maxConversations
      }
      conversationsRemaining
    }
  }
}

{
  "Authorization": "Bearer ..."
}
```

#### Chat Mutations

```graphql
1)

mutation {
  createConversation(title: "New Discussion", memberIds: ["2", "3"]) {
    conversation {
      id
      title
      owner {
        userName
      }
      members {
        userName
        firstName
      }
    }
  }

{
  "Authorization": "Bearer ..."
}

2)

mutation {
  sendMessage(
    conversationId: "1"
    text: "text"
  ) {
    message {
      id
      text
      sender {
        userName
      }
      createdAt
    }
  }
}

{
  "Authorization": "Bearer ..."
}

3)

mutation {
  addUserToConversation(
    conversationId: "1",
    userId: "3"
  ) {
    success
    message
    conversation {
      title
      members {
        userName
      }
    }
  }
}

{
  "Authorization": "Bearer ..."
}
```

### Core Queries

#### User Queries

```graphql
query GetMyInfo {
  me {
    id
    userName
    email
    firstName
  }
}

{
  "Authorization": "Bearer ..."
}
```

#### Subscription Queries

```graphql
1)

query GetSubscriptionPlans {
  subscriptionPlans {
    id
    name
    description
    maxCharacters
    maxConversations
    price
    isActive
    isDefault
  }
}

2)
query GetMySubscription {
  mySubscription {
    id
    plan {
      id
      name
      maxCharacters
      maxConversations
    }
    conversationsRemaining
  }
}

{
  "Authorization": "Bearer ..."
}
```

#### Chat Queries

```graphql
1)

query {
  conversations {
    id
    title
    owner {
      userName
    }
    members {
      userName
    }
  }
}

{
  "Authorization": "Bearer ..."
}

2)

query {
  conversation(id: "2") {
    id
    title
    owner {
      userName
    }
    members {
      userName
    }
  }
}

{
  "Authorization": "Bearer ..."
}
```
