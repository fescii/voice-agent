# **Ringover API Integration and Real-Time Audio Streaming Capabilities**

This report provides a comprehensive overview of the Ringover Application Programming Interfaces (APIs), detailing their functionalities, authentication mechanisms, and, critically, the methods for accessing real-time audio streams during active calls. The information is intended for software developers and technical architects aiming to integrate Ringover's telephony features into their applications.

## **I. Introduction to Ringover APIs**

**A. Overview of Ringover API Capabilities**

The Ringover APIs offer a programmatic gateway to the Ringover communication platform, enabling developers to integrate its functionalities with a wide array of business tools and custom software solutions. Core capabilities include comprehensive call management, synchronization of contact data, retrieval of user information, and access to Interactive Voice Response (IVR) system details.1 These APIs are instrumental in automating workflows and centralizing communication data, as demonstrated by existing integrations with Customer Relationship Management (CRM) systems like Front 3, analytics platforms such as Plecto 4, helpdesk software like Crisp 5, and integration platforms like Tray.io.2

Through the APIs, applications can perform actions such as programmatically initiating calls, dispatching SMS messages, fetching detailed call logs, managing contact lists, and receiving instantaneous notifications about various call-related events by means of webhooks.2 While some overview documents 6 provide limited summaries, the collective body of available information, including support documentation and integration guides, confirms a rich feature set designed for extensive third-party application development.

**B. API Architecture and Base URL**

The Ringover API adheres to the Representational State Transfer (REST) architectural style. For its version 2, the designated base URL for all API requests is https://public-api.ringover.com/v2.2 This URL serves as the foundation for constructing specific endpoint requests. For instance, to retrieve a list of calls, a developer would issue an HTTP GET request to the /calls path, appended to this base URL.2

**C. Documentation Landscape**

The official developer portal for Ringover API information is located at https://developer.ringover.com/.6 However, it has been observed that finding exhaustive details for certain functionalities solely within this portal can be challenging, as some overview pages provide limited information.6 Consequently, developers may find it necessary to consult a broader range of resources. This includes Ringover's support articles (often found under support.ringover.com) and documentation provided by third-party services that integrate with Ringover, or even community-driven projects such as specific GitHub repositories. This distributed nature of information means that a thorough understanding often requires synthesizing details from these varied sources to achieve a complete operational picture of the API's capabilities, particularly for advanced features like real-time audio streaming 8 or nuanced webhook configurations.7

## **II. Authentication and Authorization**

**A. API Key Generation**

Authentication with the Ringover API is primarily managed using API keys. The process for obtaining an API key is straightforward: users must log into their Ringover Dashboard, navigate to the "Developer" section, and then select the option to "Create an API key".1 This procedure is consistently described across multiple informational sources, underscoring its standard nature. Once generated, the API key must be copied and stored securely, as it is the credential used to authorize API requests. While some external systems integrating with Ringover, such as Odoo, might present their own user interface for key generation, the underlying principle remains the creation of a unique key for authenticating API interactions.9

**B. Assigning Rights/Permissions**

A critical step during API key creation is the assignment of appropriate "Rights" or permissions.1 This mechanism allows for granular control over what data and operations an API key can access. For example, an integration with the Crisp helpdesk system requires specific read/write permissions for "Monitoring," "Calls," "Contacts," and "Numbers," along with read permissions for "Users".5 Similarly, for an integration with the Plecto analytics platform, it is necessary to ensure that the API key has "read access" for all relevant metrics.4

This ability to define specific permissions for each API key is a significant security feature. It enables adherence to the principle of least privilege, where an API key is granted only the access minimally required for its intended purpose. Developers must therefore carefully evaluate the scope of their integration to request only the necessary permissions, thereby reducing the potential impact of a compromised key.

**C. Using the API Key**

The generated API key is used to authenticate requests made to the Ringover API. Typically, this key is included within the HTTP headers of each API request. While the exact header name (e.g., Authorization: Bearer \<API\_KEY\> or a custom header like X-API-Key: \<API\_KEY\>) is not explicitly specified in all contexts, the Tray.io integration documentation refers to it simply as 'API Key' during its authentication setup process.2

**D. Two-Factor Authentication (Account Security)**

While not a direct component of the API call authentication process itself, Ringover enhances overall account security through the availability of two-factor authentication (2FA) by email for user dashboard logins.10 This 2FA mechanism is triggered when a login attempt occurs from a new or unrecognized IP address. By adding an extra layer of verification for accessing the Ringover dashboard—the very place where API keys are managed and generated—2FA indirectly fortifies the security of API integrations. A more secure dashboard environment reduces the risk of unauthorized access to API credentials, thereby protecting the integrations that rely on them.

## **III. Core API Functionalities**

The Ringover API exposes a range of functionalities designed to manage communications, contacts, and system configurations.

**A. Call Management**

The API provides several endpoints and mechanisms for call management, although a complete list of specific endpoint paths beyond /calls 2 is not exhaustively detailed in all readily available documentation. Based on webhook event structures and general descriptions, the call management capabilities include:

* **Retrieving Call Information:**  
  * Fetching multiple call objects using filter parameters via a GET request to /calls.2  
  * Obtaining a specific call object using its call\_uuid.6  
  * Retrieving specific "moments" or segments within a call, also identified by call\_uuid.6  
* **Initiating Calls:** The ability to initiate outbound calls (often referred to as "click-to-call") is a fundamental feature, implied by integrations with platforms like Front, which allow users to place calls directly from the CRM interface.3  
* **In-Call Controls:** Several in-call actions can be triggered. These are often listed as "postEvent" actions, suggesting they might be invoked via specific API calls or through a webhook-like interaction model in response to certain call states 6:  
  * Mute/unmute a channel.  
  * Place a channel on hold or resume.  
  * Enable/disable call recording for a channel.  
  * Hang up a specific channel.  
  * Transfer a channel to another number or agent.  
  * Send DTMF (Dual-Tone Multi-Frequency) signals on a channel.  
* **Call Summaries:** The API can provide summaries of calls, including AI-generated summaries (e.g., using ChatGPT technology) identified by call\_uuid.6

It is worth noting that some general documentation overviews may lack specific endpoint details for actions like initiating calls or fetching detailed call logs 6, further highlighting the potential need to consult broader resources.

**B. Contact Management**

The API facilitates comprehensive contact management:

* Listing contacts, with support for pagination and alphabetical ordering to handle large datasets efficiently.2  
* Retrieving a specific contact by their ID.  
* Creating new contacts.  
* Updating existing contact details, including last name, first name, company affiliation, and phone numbers.  
* Deleting contacts.  
* Adding new phone numbers to existing contact records.11

**C. User and IVR Information**

The API allows for querying user-related and IVR configuration data:

* Retrieving the presence status of users (e.g., available, busy, offline).6  
* Accessing detailed information about IVRs, such as their unique ID, associated phone numbers, and the configured scenarios or call flows.6

**D. Messaging**

Messaging capabilities are also supported:

* Sending SMS messages to contacts.3  
* Sending chat messages, though the precise channel (e.g., SMS, internal chat) for this action may vary based on context.6

**E. Tag Management**

The API supports the use of tags for organizing and categorizing information:

* Creating new tags.  
* Retrieving a list of all available tags.  
* Fetching a specific tag by its identifier.6  
* Tags can be associated with various entities within Ringover, such as conference calls.6

## **IV. Real-time Event Notifications with Webhooks**

Webhooks are a fundamental component of the Ringover API ecosystem, enabling applications to receive real-time notifications about events occurring within a Ringover account.

**A. Purpose and Benefits**

Webhooks operate by sending an HTTP POST request containing event data to a pre-configured URL provided by the developer.7 This mechanism allows applications to react instantaneously to significant events—such as incoming calls, missed calls, new voicemails, or answered calls—without the need for continuous polling of API endpoints. The primary benefits include the ability to automate subsequent actions, maintain data synchronization with external systems like CRMs (e.g., automatically logging call details), trigger workflows in support systems, or feed data into analytics and business intelligence tools.7

**B. Configuration**

The configuration of webhooks is performed within the Ringover Dashboard, typically under a "Developer" section, then "Webhooks".7 Users select the specific events for which they wish to receive notifications and then provide the endpoint URL of their application that will receive these POST requests. This endpoint must be capable of processing incoming JSON data.7

Guides for integrating Ringover with third-party services, such as Plecto 4 or Crisp 5, often provide specific instructions for webhook setup. These may involve manual activation steps and particular URL formatting, sometimes incorporating unique credential identifiers (UUIDs) from the third-party system into the webhook URL configured in Ringover. For instance, the Plecto integration requires constructing a webhook URL using a Plecto credential UUID and then pasting this URL into the Ringover configuration for events like "Calls ringing," "Calls answered," and "Calls ended".4

**C. Key Call Events and Payload Structure**

Ringover supports a variety of webhook events. Common events include notifications for:

* Incoming calls (calls.ringing, incoming\_call)  
* Answered calls (calls.answered)  
* Ended calls (calls.ended)  
* Missed calls  
* New voicemails (voicemail)  
* IVR scenario events (scenario)  
* After-call work events  
* Contact-related call events (contact.call).4

The payload sent with each webhook is in JSON format. An example payload for an incoming\_call event is as follows 7:

JSON

{  
  "event": "incoming\_call",  
  "call\_id": "12345abcde",  
  "caller\_number": "+34123456789",  
  "receiver\_number": " \+34987654321 ",  
  "timestamp": "2024-06-17T15:30:00Z"  
}

Typically, the payload includes the event type, unique identifiers for the call, the phone numbers involved (caller and receiver), and a timestamp indicating when the event occurred.7 For enhanced security and to ensure the authenticity of incoming webhook notifications, it is advisable to verify signatures, such as HMAC signatures. Implementations like the ringover-webhooks project on GitHub demonstrate handling various webhook events, including signature verification.12

**D. Webhooks vs. Audio Stream**

A crucial distinction for developers to understand, especially those interested in real-time audio processing, is that Ringover webhooks deliver *event notifications and metadata* about calls. They inform an application that a call has started, who is calling whom, when a call ended, etc. However, webhooks do *not* transmit the actual audio stream of the call itself. The payload examples and descriptions consistently show metadata fields 7, with no indication of audio data being part of the webhook. Therefore, while webhooks are essential for knowing *when* a call is active and *which* call might be a candidate for audio streaming, they are not the mechanism for *accessing* the audio content. A separate mechanism is required for obtaining the real-time audio, as will be discussed in the next section.

**Table 1: Key Ringover Webhook Events**

To assist developers in planning their webhook integrations, the following table summarizes common Ringover webhook events and typical payload information.

| Event Name (Example) | Description | Key Payload Fields (Typical) |
| :---- | :---- | :---- |
| incoming\_call | Notifies when a new call is initiated/ringing. | event, call\_id, caller\_number, receiver\_number, timestamp |
| calls.answered | Notifies when a call is answered. | event, call\_id, answered\_by\_user\_id, timestamp |
| calls.ended | Notifies when a call has concluded. | event, call\_id, duration, reason, timestamp |
| voicemail | Notifies when a new voicemail has been received. | event, call\_id, voicemail\_url, duration, timestamp |
| missed\_call | Notifies about a call that was not answered. | event, call\_id, caller\_number, timestamp |
| scenario | Notifies about events within an IVR scenario. | event, call\_id, scenario\_id, step\_id, data |

*Note: Specific event names and payload fields may vary. Consult the latest Ringover developer documentation for precise details.*

## **V. Accessing Real-Time Audio Streams**

A primary requirement for advanced telephony integrations is the ability to access the raw audio stream of a call in real-time, for purposes such as live transcription, sentiment analysis, or integration with voice biometrics.

**A. The Challenge: Direct API vs. Specialized Solutions**

Standard Ringover REST API documentation does not prominently feature endpoints for directly accessing raw, real-time audio streams during an ongoing call. While there are discussions of "real-time voice generation API" in contexts like Text-to-Speech (TTS) services (e.g., Play.ai or Bland AI for voice chatbots 13), this refers to synthesizing audio from text, which is distinct from capturing the audio of an active phone conversation.

**B. Primary Solution: ringover-streamer (WebSocket Implementation)**

The most direct and explicitly documented method for obtaining real-time audio from Ringover calls appears to be through the ringover-streamer project, available on GitHub.8 This project is specifically engineered to "receive realtime RTP from Ringover media servers" by establishing a WebSocket connection.

* **Functionality:**  
  * **WebSocket Server:** The ringover-streamer includes a WebSocket server component that connects to Ringover's media infrastructure. This connection facilitates the reception of Real-time Transport Protocol (RTP) packets, which carry the actual audio data of the call.8  
  * **Voicebot Capabilities:** Beyond simply receiving audio, this solution enables bidirectional interaction. The application using ringover-streamer can send events and commands back to Ringover through the same WebSocket connection. This allows for the implementation of voicebot functionalities, where the application can, for example, play audio prompts into the call or react to spoken input by sending DTMF tones.8  
* **Setup and Installation:**  
  * The ringover-streamer project requires Python 3.8 or newer.  
  * Installation typically involves:  
    1. Cloning the GitHub repository: git clone \<repository-url\>  
    2. Navigating into the project directory: cd \<project-directory\>  
    3. Installing the necessary Python dependencies: pip install \-r requirements.txt  
  * The application can then be run using a ASGI server like Uvicorn (e.g., uvicorn app:app \--host 0.0.0.0 \--port 8000 \--reload) or directly via Python (e.g., python app.py).8  
* **How it Works (Interacting with the Streamer):**  
  * **Receiving Audio:** Once the WebSocket connection is established by the ringover-streamer, it begins receiving RTP audio from Ringover's media servers. RTP is a standard protocol for delivering audio and video over IP networks and typically carries raw audio codecs (such as G.711, Opus, etc.). The application would then process these RTP packets to reconstruct the audio stream.  
  * **Sending Events/Commands back to Ringover via WebSocket:** The ringover-streamer also defines a set of JSON-based commands that the developer's application can send over the WebSocket to Ringover to interact with the call 8:  
    * **Play Audio:** Instructs Ringover to play an audio file (e.g., a pre-recorded prompt) into the call.  
      JSON  
      { "event": "play", "file": "https://example.com/audio.mp3" }

    * **Stream Audio (Injecting Audio):** Allows the application to send its own audio data (base64 encoded) to be played into the call. This is key for voicebots that generate dynamic responses.  
      JSON  
      {  
        "type": "streamAudio",  
        "data": {  
          "audioDataType": "raw", // Supported: raw, mp3, wav, ogg  
          "sampleRate": 8000,     // Supported: 8000, 16000, 24000 Hz  
          "audioData": "base64\_encoded\_audio\_data\_here"  
        }  
      }

    * **Break:** Sends a command to stop any ongoing audio streaming or playback initiated by play or streamAudio.  
      JSON  
      { "event": "break" }

    * **Digits (DTMF):** Sends DTMF tones into the call, useful for interacting with IVR menus or other automated systems.  
      JSON  
      { "event": "digits", "data": 123 } // 'data' contains the digits

    * **Transfer:** Initiates a call transfer to a specified number.  
      JSON  
      { "event": "transfer", "data": "number\_to\_transfer\_to" }

The use of ringover-streamer signifies a shift from the typical request-response pattern of REST APIs to a persistent, bidirectional communication channel provided by WebSockets.14 This has important architectural implications for the consuming application, which must manage the WebSocket connection's lifecycle, handle asynchronous messages (both incoming audio data and outgoing commands), and maintain state as needed.

Furthermore, the ringover-streamer being a GitHub project, even if officially supported or provided by Ringover, suggests it is a specialized tool or SDK rather than a standard, hosted API endpoint within the public-api.ringover.com domain. The requirement for developers to clone, install dependencies, and run this server component themselves 8 indicates a different operational model. The developer takes on the responsibility of deploying and managing this streamer application, which then interfaces with Ringover's backend. The project's BSD License also aligns with this model of a distributable software component.8

**Table 2: ringover-streamer WebSocket Event Commands (Application to Ringover)**

This table details the commands an application can send to Ringover via the WebSocket connection established by ringover-streamer.

| Command (event or type) | Purpose/Description | JSON Payload Format (Example) | Key Parameters/Notes |
| :---- | :---- | :---- | :---- |
| play | Plays a remote audio file into the call. | {"event": "play", "file": "URL\_to\_audio\_file"} | file: URL of the audio file (e.g., MP3). |
| streamAudio | Streams base64 encoded audio data into the call. | {"type": "streamAudio", "data": {"audioDataType": "raw", "sampleRate": 8000, "audioData": "base64\_string"}} | audioDataType: raw, mp3, wav, ogg. sampleRate: 8000, 16000, 24000 Hz. audioData: Base64 encoded audio. |
| break | Stops current audio playback/streaming in the call. | {"event": "break"} | None. |
| digits | Sends DTMF digits into the call. | {"event": "digits", "data": 123} | data: The sequence of digits to send. |
| transfer | Transfers the call to a specified phone number. | {"event": "transfer", "data": "destination\_number"} | data: The phone number to transfer the call to. |

*Source: Based on information from the ringover-streamer project.8 Developers should refer to the project's latest documentation for the most current command set and specifications.*

## **VI. Practical Considerations and Best Practices**

When integrating with Ringover APIs and the ringover-streamer, several practical aspects and best practices should be considered.

**A. Error Handling**

For interactions with the REST API, applications should implement robust error handling by checking HTTP status codes on responses and parsing any error messages provided in the response body. For the WebSocket-based ringover-streamer, error handling must cover the WebSocket connection lifecycle (e.g., connection failures, unexpected closures) and any error messages or statuses returned in response to commands sent over the WebSocket. (Specific error code details were not extensively covered in the provided materials, so developers should consult Ringover's comprehensive documentation).

**B. Rate Limits**

Public APIs often implement rate limits to ensure fair usage and maintain service stability. While specific rate limit figures for the Ringover API were not detailed in the available information, developers anticipating high volumes of API calls should consult Ringover's official documentation or contact their support to understand any applicable limits and design their applications accordingly to handle potential rate-limiting responses (e.g., HTTP 429 Too Many Requests).

**C. Security for API Keys and Webhook URLs**

* **API Keys:** API keys are sensitive credentials and must be protected. They should be stored securely (e.g., in environment variables or a secure vault system) and never embedded directly in client-side code or committed to version control repositories.  
* **Webhook URLs:** Webhook endpoint URLs configured in Ringover should use HTTPS to ensure that event data transmitted from Ringover to the application is encrypted in transit.7  
* **Webhook Authenticity:** It is crucial to verify the authenticity of incoming webhook requests to prevent spoofing attacks, where an attacker might send malicious payloads to the webhook endpoint. One common method is to use HMAC (Hash-based Message Authentication Code) signatures. The ringover-webhooks GitHub project implies the use of such verification.12 Developers should implement a verification mechanism based on a shared secret or other method provided by Ringover.

**D. Safari Cross-Site Tracking Prevention**

A specific client-side consideration arises for Computer Telephony Integrations (CTIs) that are used within Apple's Safari browser. Due to Safari's privacy features, users might need to disable the "Prevent cross-site tracking" option in Safari's privacy settings to ensure full functionality of the CTI.7 Integrators should be aware of this and potentially inform their users if Safari is a target browser.

**E. Data Synchronization and Consistency**

When integrating Ringover data with external systems (e.g., CRMs, databases), it is important to understand the data update model. Ringover integrations often utilize a hybrid approach:

* **Real-time Updates:** Critical call events are typically pushed in real-time or near real-time via webhooks (e.g., "Calls ringing" notifications for the Plecto integration are instant via webhooks 4).  
* **Periodic Polling:** For other data types, or as a fallback, periodic polling of API endpoints might be necessary (e.g., Plecto's integration notes that "Call Logs" update every 5 minutes and "Surveys" every 2 hours, without explicit webhook support mentioned for these specific data types in that context 4).

This hybrid model means developers need to design their integration logic to accommodate both immediate webhook-driven updates and scheduled polling for other data entities. This understanding is key to setting correct expectations regarding data freshness and ensuring consistency across integrated systems.

## **VII. Conclusion and Summary of Key Findings**

The Ringover API suite provides a robust platform for developers to integrate advanced telephony functionalities into their applications. Key strengths lie in comprehensive call management, contact synchronization, messaging capabilities, and powerful event-driven automation through webhooks. These features enable the creation of deeply integrated solutions that can enhance business workflows and data centralization.

For the specific requirement of accessing real-time audio streams during calls, the primary solution identified is the ringover-streamer GitHub project.8 This tool leverages WebSockets to receive RTP audio from Ringover's media servers and allows for bidirectional communication, enabling voicebot-like interactions. This approach differs significantly from standard REST API interactions, requiring developers to manage persistent WebSocket connections and a specialized server component.

It is evident that obtaining a complete understanding of Ringover's API capabilities, particularly for advanced or specialized features, may necessitate consulting a range of resources beyond the main developer portal. This includes support articles, third-party integration guides, and community projects like the ringover-streamer.

Finally, a clear distinction must be maintained: webhooks are invaluable for receiving real-time *metadata* and notifications about call events, which can trigger workflows or alert applications to active calls. However, for accessing the *actual audio content* of those calls in real-time and for interactive call control at the audio level, the WebSocket-based ringover-streamer is the indicated pathway. Developers should choose the appropriate mechanism based on whether their application needs event notifications or direct audio stream access and control.

#### **Works cited**

1. Using our API \- Ringover Help Center, accessed June 8, 2025, [https://support.ringover.com/hc/en-us/articles/15206971712657-Using-our-API](https://support.ringover.com/hc/en-us/articles/15206971712657-Using-our-API)  
2. Ringover | Connectors | Tray Documentation, accessed June 8, 2025, [https://tray.ai/documentation/connectors/service/ringover/](https://tray.ai/documentation/connectors/service/ringover/)  
3. Front Phone System Integration (VoIP / Dialer) \- Ringover, accessed June 8, 2025, [https://www.ringover.com/integration-front](https://www.ringover.com/integration-front)  
4. Ringover Integration \- Plecto Docs, accessed June 8, 2025, [https://docs.plecto.com/kb/guide/en/ringover-8z2xogEASf/Steps/2386577](https://docs.plecto.com/kb/guide/en/ringover-8z2xogEASf/Steps/2386577)  
5. How to connect Ringover with Crisp?, accessed June 8, 2025, [https://help.crisp.chat/en/article/how-to-connect-ringover-with-crisp-r8u84t/](https://help.crisp.chat/en/article/how-to-connect-ringover-with-crisp-r8u84t/)  
6. Ringover API Documentation, accessed June 8, 2025, [https://developer.ringover.com/](https://developer.ringover.com/)  
7. Using our webhooks \- Ringover Help Center, accessed June 8, 2025, [https://support.ringover.com/hc/en-us/articles/15206913970577-Using-our-webhooks](https://support.ringover.com/hc/en-us/articles/15206913970577-Using-our-webhooks)  
8. ringover/ringover-streamer \- GitHub, accessed June 8, 2025, [https://github.com/ringover/ringover-streamer](https://github.com/ringover/ringover-streamer)  
9. How to generate the API key in Odoo \- Ringover Help Center, accessed June 8, 2025, [https://support.ringover.com/hc/en-us/articles/23486965065233-How-to-generate-the-API-key-in-Odoo](https://support.ringover.com/hc/en-us/articles/23486965065233-How-to-generate-the-API-key-in-Odoo)  
10. Activate two-factor authentication by email \- Ringover Help Center, accessed June 8, 2025, [https://support.ringover.com/hc/en-us/articles/24229088391697-Activate-two-factor-authentication-by-email](https://support.ringover.com/hc/en-us/articles/24229088391697-Activate-two-factor-authentication-by-email)  
11. How to integrate Webhook / API Integration & Ringover | 1 click ▶️ integrations \- Integrately, accessed June 8, 2025, [https://integrately.com/integrations/ringover/webhook-api](https://integrately.com/integrations/ringover/webhook-api)  
12. ringover/ringover-webhooks \- GitHub, accessed June 8, 2025, [https://github.com/ringover/ringover-webhooks](https://github.com/ringover/ringover-webhooks)  
13. The Advantages of an AI Voice Chatbot to Automate Your Customer Relations \- Ringover, accessed June 8, 2025, [https://www.ringover.com/blog/voice-chatbot](https://www.ringover.com/blog/voice-chatbot)  
14. The WebSocket API (WebSockets) \- Web APIs \- MDN Web Docs, accessed June 8, 2025, [https://developer.mozilla.org/en-US/docs/Web/API/WebSockets\_API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)