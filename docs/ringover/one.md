# **Integrating Ringover APIs for Real-Time Audio Streaming and Enhanced Call Control**

This report provides a comprehensive guide to utilizing Ringover's Application Programming Interfaces (APIs) and associated tools to achieve real-time audio streaming during calls and implement advanced call control functionalities. It details the necessary prerequisites, authentication procedures, webhook configurations, and the integration of the ringover-streamer project for direct audio access and voicebot capabilities.

## **I. Introduction to Ringover's Real-Time Communication Capabilities**

Ringover offers a suite of tools and APIs enabling developers to integrate telephony features into their applications, with a particular focus on managing call data and facilitating real-time interactions. Understanding the distinct roles of its REST API, the ringover-streamer project, and webhooks is crucial for effectively implementing real-time audio solutions.

### **A. Overview of Ringover APIs and their Relevance to Real-Time Audio**

The Ringover Public API is primarily a RESTful interface. It is designed to allow applications to retrieve phone-related information, access details about contacts, users, and groups, and manage their properties through standard HTTP commands.1 While this API facilitates various data retrieval tasks and enables certain call control actions—such as sending DTMF signals or initiating call transfers via specific POST event requests 1—it is not inherently designed for direct, continuous real-time audio streaming.

The architecture of Ringover's communication offerings separates general data management and control API operations from specialized real-time media handling. REST APIs, by their request-response nature, are not optimally suited for the continuous, low-latency demands of media streams like those using Real-time Transport Protocol (RTP). For such purposes, specialized protocols like WebSockets (for signaling and control) and RTP (for media transport) are more effective. This architectural separation allows Ringover to optimize each component: a robust REST API for management tasks and dedicated mechanisms, such as the ringover-streamer project, for performance-critical media streaming. Consequently, developers aiming to implement real-time audio functionalities will typically need to interact with both the Ringover REST API (for call metadata, initiating calls, or post-call analysis) and a separate mechanism for accessing the audio stream itself.

### **B. The Pivotal Role of ringover-streamer and Webhooks in Achieving Real-Time Functionality**

For direct access to real-time audio, the ringover-streamer project is a key component. This open-source tool, available on GitHub, is specifically engineered to "receive real-time RTP (Real-time Transport Protocol) from Ringover media servers" through a WebSocket connection.2 Beyond merely receiving audio, ringover-streamer also enables applications to send interactive responses, effectively transforming the connected application into a voicebot.

Complementing the ringover-streamer are Ringover's webhooks. Webhooks deliver real-time *event notifications*—such as call ringing, call answered, or call ended—to a specified URL.3 While webhooks do not transport the audio stream, they are indispensable for knowing *when* to initiate, manage, or terminate an audio stream. They also serve as triggers for other automated workflows in response to call lifecycle events.

These two components, ringover-streamer and webhooks, are not mutually exclusive but rather work in tandem to provide a comprehensive real-time solution. For instance, a webhook notification indicating the start of a call can trigger an application to instruct ringover-streamer to connect and begin streaming audio for that particular call. The ringover-streamer then manages the continuous flow of audio data, a task for which webhooks are not designed. Similarly, a webhook can signal the end of a call, prompting the application to cease audio processing. This synergistic relationship allows for the development of more reactive and efficient systems, avoiding the need for an application to, for example, maintain an idle ringover-streamer connection while waiting for a call if a webhook can announce the call's initiation.

## **II. Getting Started: Prerequisites and Authentication**

Before integrating Ringover's real-time capabilities, it is essential to understand the subscription requirements for API and webhook access, and the process for obtaining and using API keys for authentication.

### **A. Ringover Subscription Plans and API/Webhook Access**

Access to Ringover's API and webhook functionalities is contingent upon the active subscription plan. Ringover offers several plans, with varying levels of access to developer tools:

* The **SMART** plan includes access to Ringover's API. This allows for data retrieval and basic integrations.4  
* The **BUSINESS** plan encompasses all features of the SMART plan and additionally provides access to Ringover's webhooks. This tier is necessary for applications requiring real-time event notifications.4  
* The **ADVANCED** plan includes all features of the BUSINESS plan, thereby offering both API and webhook access for the most comprehensive integration capabilities.4

Pricing for these plans varies, with options for monthly or annual billing. For example, the Smart plan starts at $21 per user/month (annual billing), the Business plan at $44 per user/month (annual billing), and the Advanced plan at $54 per user/month (annual billing).4

This tiered access model means that full real-time capabilities, particularly those leveraging webhooks for event-driven actions, necessitate at least the BUSINESS plan. Webhooks, which enable more advanced and reactive integrations, may generate a higher server-side load for Ringover, justifying their inclusion in higher-tier plans. Basic API access, being more fundamental for many integrations, is offered at a lower tier. While the ringover-streamer tool itself is open-source, its utility is significantly enhanced when combined with webhook-driven call event notifications. Developers must therefore carefully evaluate their Ringover subscription plan based on the specific requirement for webhook functionality.

**Table 1: Ringover Subscription Plan API/Webhook Access Comparison**

| Plan Name | Example Price (Annual Billing, per user/month) | API Access | Webhook Access | Key Developer Features |
| :---- | :---- | :---- | :---- | :---- |
| Smart | $21 4 | Yes 4 | No 4 | Access to Ringover REST API for data retrieval (calls, contacts, users, IVR).4 |
| Business | $44 4 | Yes 4 | Yes 4 | All SMART plan features plus access to Webhooks for real-time event notifications (e.g., call answered, ended).4 |
| Advanced | $54 4 | Yes 4 | Yes 4 | All BUSINESS plan features, providing the most comprehensive API and webhook integration capabilities.4 |

### **B. Obtaining Your Ringover API Key: A Step-by-Step Guide**

An API Key is mandatory for authenticating requests made to the Ringover API. The process for acquiring an API key is straightforward:

1. Log into the Ringover dashboard.  
2. Navigate to the "Developer" tab. This is sometimes accessed by clicking on a "Crown" icon that leads to the Dashboard sections.5  
3. Within the Developer section, API keys can be found in a list, or new ones can be generated by clicking an option such as "Create an API key".5  
4. When generating a key, it is often possible to associate specific rights and concerned users with that key, allowing for granular control over its permissions.7

This ability to define specific rights for each API key is a significant feature for security and operational management. It aligns with the principle of least privilege, ensuring that an application or integration only has the permissions it absolutely requires to function. This practice minimizes the potential impact if an API key were to be compromised. Furthermore, different applications or services within an organization might legitimately require different levels of access, which can be managed through distinct keys with tailored permissions. Developers are strongly advised to create unique API keys with the minimum necessary permissions for each distinct application or service they build, rather than relying on a single, overly permissive key.

### **C. Authenticating API Requests**

Once an API key is obtained, it must be included in requests to the Ringover API. The Ringover API base URL is https://public-api.ringover.com/v2.5 While the specific method of including the API key (e.g., as an Authorization header or a query parameter) is not explicitly detailed in all provided materials for all API interactions, standard REST API practices typically involve using a Bearer token in the Authorization header (e.g., Authorization: Bearer \<YOUR\_API\_KEY\>).

The ringover-streamer project, which utilizes WebSockets, may have its own specific authentication requirements for establishing its connection to Ringover's media servers. This could involve using the API key directly during the WebSocket handshake or using it to obtain a session-specific token. Developers should consult the main Ringover API documentation for precise instructions on formatting authentication headers for REST calls and investigate the ringover-streamer documentation or source code for its specific WebSocket authentication mechanisms.

## **III. Real-Time Call Event Notifications with Webhooks**

Ringover webhooks are a powerful mechanism for receiving real-time notifications about call-related events, enabling applications to react instantly and automate workflows.

### **A. Understanding Ringover Webhooks**

Webhooks function by Ringover sending HTTP POST requests, containing JSON-formatted data, to a user-specified URL whenever a designated event occurs within the Ringover account.3 This system allows for the automation of actions, seamless integration of Ringover with other business tools (such as CRMs or customer support platforms), and the general optimization of telephony-related workflows.3

The range of events for which notifications can be received is extensive, including but not limited to:

* Incoming calls  
* Missed calls  
* Voicemail messages  
* Answered calls  
* Call duration information 3

These webhooks serve as the reactive backbone for call-related automation. They provide the real-time triggers necessary for applications to respond immediately to events as they happen. This approach decouples the developer's application from the need to continuously poll the Ringover API for status updates, which is an inefficient and resource-intensive practice. The JSON payload delivered with each webhook contains the essential context—such as call identifiers and involved phone numbers—allowing the receiving application to take specific, informed actions. This capability allows developers to construct sophisticated systems, for example, to automatically log call details into a CRM when an answered\_call event is received, trigger a follow-up task for a missed\_call event, or initiate a transcription service upon receipt of a voicemail\_message event.

### **B. Configuring Webhooks in the Ringover Dashboard**

Setting up webhooks to receive these notifications involves a configuration process within the Ringover dashboard:

1. **Access Developer Settings:** Navigate to the Ringover Dashboard, then go to the "Developer" section and select "Webhooks".3  
2. **Select Events:** Enable the specific events for which notifications are desired. Options typically include "Incoming call," "Missed call," "Voicemail," and "Answered call," among others relevant to business needs.3  
3. **Enter Webhook URL:** Input the URL of the server or application endpoint that will receive these notifications. This URL must be publicly accessible.3  
4. **Ensure Endpoint Readiness:** Crucially, the provided URL must be configured to accept HTTP POST requests and be capable of processing data in JSON format.3

For users employing a CTI (Computer Telephony Integration) solution within the Safari browser, a special configuration may be necessary: open Safari's settings, navigate to the "Privacy" tab, and uncheck the "Prevent cross-site tracking" option to ensure correct functionality.3 This practical tip can prevent troubleshooting headaches for developers working in that specific environment.

It is vital to understand that configuring the URL in the Ringover dashboard is only one part of the setup. The developer must implement a robust listener service at the specified URL. This service is responsible for receiving the incoming POST requests, parsing the JSON payload, handling any potential errors gracefully, and executing the subsequent business logic. Webhooks are typically a "fire-and-forget" mechanism from the sender's perspective (Ringover, in this case), so the reliability and correctness of the receiving endpoint are paramount. Security considerations for this endpoint, such as ensuring it uses HTTPS and potentially validating the source of incoming requests, should also be addressed.

### **C. Subscribable Events and Payload Structures**

Ringover provides notifications for several key call events. The data sent in the webhook payload offers the context needed for applications to act. For instance, an incoming\_call event payload might look like this:

JSON

{  
  "event": "incoming\_call",  
  "call\_id": "12345abcde",  
  "caller\_number": "+34123456789",  
  "receiver\_number": " \+34987654321 ",  
  "timestamp": "2024-06-17T15:30:00Z"  
}

*3*

The information contained within this payload is critical. The call\_id is essential for correlating this event with other API calls or, importantly, with an audio stream that might be managed via ringover-streamer. The caller\_number and receiver\_number allow for customized responses, lookups in a CRM, or specific routing logic. The timestamp is vital for accurate logging, sequencing events, and audit trails. Developers must design their webhook handling logic to meticulously parse these fields and use them to drive appropriate application behavior.

**Table 2: Ringover Webhook Event Payloads (Illustrative Examples)**

| Event Name | Description | Key Fields in JSON Payload | Example Value/Format (from ) |
| :---- | :---- | :---- | :---- |
| incoming\_call | Notification of an incoming call. | event, call\_id, caller\_number, receiver\_number, timestamp | See JSON example above |
| answered\_call | Notification when a call is answered. | Similar to incoming\_call, specific fields TBD | (Payload structure varies per event type) |
| missed\_call | Notification of a call that was not answered. | Similar to incoming\_call, specific fields TBD | (Payload structure varies per event type) |
| voicemail\_message | Notification when a new voicemail is received. | Similar to incoming\_call, specific fields TBD | (Payload structure varies per event type) |
| call\_ended | Notification when a call has concluded. | Similar to incoming\_call, specific fields TBD | (Payload structure varies per event type) |

*Note: The exact payload structure for all event types should be verified against the official Ringover developer documentation.*

## **IV. Implementing Real-Time Audio Streaming with ringover-streamer**

The ringover-streamer project is a cornerstone for applications requiring direct access to real-time call audio and the ability to interact with calls programmatically, such as in voicebot scenarios.

### **A. Deep Dive into the ringover-streamer Project**

The primary purpose of the ringover-streamer is to provide a complete WebSocket streamer implementation. This allows a user's application to receive real-time RTP (Real-time Transport Protocol) audio from Ringover's media servers. Furthermore, it enables the application to send events back to the Ringover system, effectively allowing it to act as a voicebot by playing audio, sending DTMF tones, or transferring calls.2

Key features include:

* A WebSocket streaming server designed to receive real-time RTP from Ringover media servers.  
* The capability to respond directly by sending various events, transforming the streamer into an interactive voice agent.2

Architecturally, ringover-streamer is a Python-based application. It establishes a WebSocket server to which the developer's application connects. This streamer application, in turn, likely handles the complex negotiation and communication with Ringover's media infrastructure to establish the RTP flow. It then relays this audio data, or events derived from it, to the connected client application via its own WebSocket interface. This project acts as an application-level bridge, abstracting away the lower-level complexities of direct RTP handling and the specifics of WebSocket communication with Ringover's media servers. By providing this abstraction, ringover-streamer significantly lowers the barrier to entry for developers looking to process or interact with real-time call audio.

### **B. Installation and Setup**

To use the ringover-streamer, a Python environment is required.

**Prerequisites:**

* Python 3.8 or higher.2  
* pip (Python package installer).2

**Installation Steps:**

1. Clone the repository from GitHub:  
   Bash  
   git clone \<repository-url\>   
   *(The specific URL can be found on the ringover/ringover-streamer GitHub page)*.2  
2. Navigate to the project directory:  
   Bash  
   cd \<project-directory\>

.2  
3\. Install the necessary dependencies:  
bash pip install \-r requirements.txt  
.2  
Running the Application:  
The application can be started using Uvicorn (an ASGI server) or directly with Python:

* Using Uvicorn (recommended for development with auto-reload):  
  Bash  
  uvicorn app:app \--host 0.0.0.0 \--port 8000 \--reload

.2

* Using Python directly:  
  Bash  
  python app.py

.2

The reliance on Python and tools like pip and Uvicorn signifies that ringover-streamer operates within the Python ecosystem. If a developer's existing project is not Python-based, they will typically run ringover-streamer as a separate, standalone service. Their application would then communicate with this service, most likely via its exposed WebSocket interface (running, by default, on port 8000). If the existing project is Python-based, a more direct integration might be possible, although running it as a distinct service often aligns well with microservice architectural patterns.

### **C. Integrating ringover-streamer into Your Existing Project**

Once ringover-streamer is running, integration involves two main aspects: receiving audio and sending commands.

Receiving Real-Time RTP Audio Streams:  
The core functionality is to "receive real-time RTP from Ringover media servers".2 The ringover-streamer application acts as a client to Ringover's media infrastructure and simultaneously as a WebSocket server to the developer's application. The developer's application connects as a client to the WebSocket endpoint exposed by ringover-streamer. The audio data is then streamed over this WebSocket connection. The precise format of this audio data (e.g., raw audio chunks, specific encoding, metadata) would need to be determined by examining the streamer's output or its documentation.  
Interacting with Calls: Sending Events:  
A key feature for interactive applications, especially voicebots, is the ability to send JSON-formatted events from the developer's application, through ringover-streamer, back to the Ringover system to control the call or inject audio. Available commands include:

* **Play:** Instructs Ringover to play an audio file to the caller.  
  JSON  
  {  
    "event": "play",  
    "file": "https://test.com/test.mp3"  
  }

.2

* **Stream:** Allows for streaming base64 encoded audio data into the call. This is useful for dynamic audio generation, such as text-to-speech output.  
  JSON  
  {  
    "type": "streamAudio",  
    "data": {  
      "audioDataType": "raw",  // Options: raw | mp3 | wav | ogg  
      "sampleRate": 8000,      // Options: 8000 | 16000 | 24000  
      "audioData": "base64 encoded audio"  
    }  
  }

.2

* **Break:** Stops any ongoing audio streaming (e.g., initiated by a "Play" or "Stream" event).  
  JSON  
  {  
    "event": "break"  
  }

.2

* **Digits:** Sends DTMF (Dual-Tone Multi-Frequency) tones, for example, to interact with an IVR system.  
  JSON  
  {  
    "event": "digits",  
    "data": 123   
  }  
  (where 123 represents the digits to send).2  
* **Transfer:** Initiates a call transfer to a specified number.  
  JSON  
  {  
    "event": "transfer",  
    "data": "number"   
  }  
  (where "number" is the destination number for the transfer).2

This bidirectional communication capability is what transforms ringover-streamer from a passive audio listener into an active participant in the call. A voicebot, for example, needs to listen to the caller (by processing the RTP audio received via the streamer), understand the intent (using speech-to-text and natural language understanding), and then respond appropriately. The "Play" event allows for pre-recorded audio responses, while the "streamAudio" event enables dynamic, synthesized speech to be injected into the call in real-time. "Digits" and "Transfer" commands provide the bot with the means to navigate automated menus or escalate the call to a human agent. Thus, ringover-streamer provides the fundamental building blocks for creating sophisticated voice-interactive applications on the Ringover platform, where the developer's existing project acts as the "brain" of the voicebot, using ringover-streamer as its "ears" and "mouth."

**Table 3: ringover-streamer Event Command Reference**

| Event Type (event or type field) | Purpose/Description | Full JSON Payload Example | Key Parameters & Options |
| :---- | :---- | :---- | :---- |
| play | Plays a specified audio file to the caller. | {"event": "play", "file": "https://example.com/audio.mp3"} | file: URL of the audio file to be played. |
| streamAudio | Streams base64 encoded audio data into the call. | {"type": "streamAudio", "data": {"audioDataType": "raw", "sampleRate": 8000, "audioData": "UklGRi..."}} | audioDataType: Format of the audio data (raw, mp3, wav, ogg). sampleRate: Sample rate of the audio (8000, 16000, 24000 Hz). audioData: Base64 encoded string of the audio. |
| break | Stops any currently playing audio stream (from play or streamAudio). | {"event": "break"} | None. |
| digits | Sends DTMF tones into the call. | {"event": "digits", "data": 1234} | data: The sequence of digits to send (e.g., 1234). |
| transfer | Transfers the call to a specified number. | {"event": "transfer", "data": "+1234567890"} | data: The phone number (string) to which the call should be transferred. |

*Payload examples and options are based on.2*

### **D. Considerations for Building Voicebot Functionalities**

While ringover-streamer provides the critical audio input/output and basic call control mechanisms for a voicebot, it is important to recognize that it is one component in a larger system. The core intelligence of a voicebot—comprising Speech-to-Text (STT) conversion, Natural Language Understanding (NLU) for intent recognition, dialog management for conversation flow, and Text-to-Speech (TTS) for generating responses—must be implemented within the developer's existing project or by integrating third-party AI/ML services.

The ringover-streamer handles the audio transport and facilitates sending predefined commands. The description "respond directly by sending events and transform the streamer to a real voicebot" 2 highlights the potential it unlocks, but the actual "transformation" into a voicebot relies on the external logic provided by the developer's application. This distinction is crucial for setting correct expectations about the capabilities of the ringover-streamer tool itself.

## **V. Leveraging Other Relevant Ringover API Endpoints**

While the primary focus of this report is on real-time audio streaming via ringover-streamer and event notifications via webhooks, the broader Ringover REST API offers complementary endpoints that can enrich an application's functionality and provide a more holistic call management solution.

### **A. Overview of Complementary API Endpoints**

The Ringover REST API can be used to access a wealth of information that provides context before, during, or after a call handled by ringover-streamer. Examples of such data include:

* **Call Logs:** Retrieving historical call data for analysis, reporting, or building a history of interactions. The GET /calls endpoint is relevant here.1  
* **User and Team Information:** Accessing details about Ringover users, their presence status, or team structures.1 This could be used, for example, to determine agent availability before attempting a transfer.  
* **Contact Management:** Interacting with contact data stored within Ringover.  
* **Call Recordings:** Accessing recordings of calls. Initial exploration did not yield specific endpoints for managing recordings directly from the primary developer portal overview.1 This suggests that functionality for accessing recordings might be found through deeper navigation of the full API documentation or could be handled via different mechanisms (e.g., recordings being pushed to a storage location or accessed via the Ringover dashboard).

Utilizing these REST API endpoints allows for more comprehensive and context-aware applications. For instance, when a call is received (notified via webhook and audio streamed via ringover-streamer), the application could query the REST API for the caller's interaction history or contact details from the CRM to personalize the voicebot's interaction. Similarly, after a call, details logged via the API can supplement any data captured during the real-time interaction. Developers should therefore explore the full Ringover API surface to understand all available data points and control mechanisms that can augment their real-time audio applications. If specific information, like call recording access methods, is not immediately apparent, the complete official API documentation is the definitive resource.

## **VI. Conclusion and Best Practices**

Successfully implementing real-time audio streaming and advanced call control with Ringover involves a multi-faceted approach, combining the strategic use of the Ringover REST API, webhooks for event notifications, and the ringover-streamer project for direct audio access.

### **A. Summary of Key Steps to Implement Real-Time Audio Streaming**

1. **Subscription Plan:** Ensure the Ringover subscription plan (e.g., BUSINESS or ADVANCED) provides the necessary API and, crucially, webhook access.4  
2. **API Key:** Obtain a Ringover API key from the developer section of the dashboard, configuring permissions appropriately.5  
3. **Webhooks (Recommended):** Configure webhooks in the Ringover dashboard to receive real-time notifications for call events (e.g., call started, call ended). This involves specifying an endpoint URL capable of handling HTTP POST requests with JSON payloads.3  
4. **ringover-streamer Setup:** Clone, install dependencies, and run the ringover-streamer Python application.2  
5. **Application Integration:** Connect the primary application to the WebSocket server exposed by ringover-streamer to receive audio data.  
6. **Audio Processing:** Implement logic in the application to process the incoming audio stream (e.g., for speech-to-text if building a voicebot).  
7. **Interactive Control:** Utilize the event-sending capabilities of ringover-streamer (e.g., play, streamAudio, digits, transfer) to interact with the call based on application logic.2

### **B. Recommendations for Robust Integration**

* **Error Handling:** Implement comprehensive error handling for all external interactions: REST API calls, webhook deliveries (acknowledging that webhooks are often "fire-and-forget" but the receiving endpoint must be robust), and WebSocket connections with ringover-streamer.  
* **Security:** Carefully safeguard API keys and secure webhook endpoints (e.g., using HTTPS and validating request origins if possible).  
* **Scalability:** If the application needs to handle a high volume of concurrent calls, evaluate the scalability of the ringover-streamer instance(s) and the application's capacity to process multiple audio streams and WebSocket connections.  
* **Logging and Monitoring:** Implement thorough logging at all stages of the integration for troubleshooting and monitoring system health. This includes logging API request/responses, received webhook payloads, and interactions with ringover-streamer.  
* **Idempotency:** For actions triggered by webhooks, consider designing handlers to be idempotent where possible, to prevent unintended side effects if a webhook is delivered more than once.

### **C. Pointers to Further Developer Resources**

The information provided in this report is based on available documentation and project resources at the time of writing. For the most current, complete, and detailed information, developers should always refer to the official Ringover resources:

* **Ringover Developer Portal:** https://developer.ringover.com/ 1 (This is the primary source for REST API documentation, webhook details, and general platform information).  
* **ringover-streamer GitHub Repository:** https://github.com/ringover/ringover-streamer 2 (The README file here is the definitive guide for this specific tool, including setup, configuration, and event formats).

While this report aims to be comprehensive, API platforms and open-source tools evolve. The official documentation will always contain the latest updates on endpoints, parameters, authentication methods, and best practices. These official sources are indispensable for aspects not exhaustively covered here, such as detailed error code explanations for the REST API or advanced configuration options for ringover-streamer.

#### **Works cited**

1. Ringover API Documentation, accessed June 8, 2025, [https://developer.ringover.com/](https://developer.ringover.com/)  
2. Ringover Streamer \- GitHub, accessed June 8, 2025, [https://github.com/ringover/ringover-streamer](https://github.com/ringover/ringover-streamer)  
3. Using our webhooks – Ringover Help Center, accessed June 8, 2025, [https://support.ringover.com/hc/en-us/articles/15206913970577-Using-our-webhooks](https://support.ringover.com/hc/en-us/articles/15206913970577-Using-our-webhooks)  
4. Unlimited Calls: VoIP International & US Calling Plans \- Ringover, accessed June 8, 2025, [https://www.ringover.com/unlimited-calls](https://www.ringover.com/unlimited-calls)  
5. Ringover | Connectors | Tray Documentation, accessed June 8, 2025, [https://tray.ai/documentation/connectors/service/ringover/](https://tray.ai/documentation/connectors/service/ringover/)  
6. Ringover Integration \- Plecto Docs, accessed June 8, 2025, [https://docs.plecto.com/kb/guide/en/ringover-8z2xogEASf/Steps/2386577](https://docs.plecto.com/kb/guide/en/ringover-8z2xogEASf/Steps/2386577)  
7. Discover Our Public API REST \- Ringover, accessed June 8, 2025, [https://www.ringover.com/public-api](https://www.ringover.com/public-api)