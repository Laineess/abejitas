

# Trust and safety
<a name="trust-safety"></a>

Users generate large amounts of text content through online applications (such as peer-to-peer chats and forum discussions), comments posted on websites, and through generative AI applications (input prompts and outputs from generative AI models). The Amazon Comprehend Trust and Safety features can help you moderate this content, to provide a safe and inclusive environment for your users. 

Benefits of using the Amazon Comprehend trust and safety features include: 
+ Faster moderation: Quickly and accurately moderate large volume of text to keep your online platforms free from inappropriate content.
+ Customizable: Customize the moderation thresholds in API responses to suit your application needs.
+ Easy to use: Configure the trust and safety features through LangChain integration or using the AWS CLI or SDKs.

Amazon Comprehend trust and safety address the following aspects of content moderation:
+ **Toxicity detection** – Detect content that may be harmful, offensive, or inappropriate. Examples include hate speech, threats, or abuse.
+ **Intent classification** – Detect content that has explicit or implicit malicious intent. Examples include discriminatory or illegal content, or content that expresses or requests advice on medical, legal, political, controversial, personal or financial subjects.
+ **Privacy protection** – Users can inadvertently provide content that may reveal personally identifiable information (PII). Amazon Comprehend PII provides the ability to detect and redact PII.

**Topics**
+ [Toxicity detection](#toxicity-detection)
+ [Prompt safety classification](#prompt-classification)
+ [PII detection and redaction](#trust-safety-pii)

## Toxicity detection
<a name="toxicity-detection"></a>

Amazon Comprehend toxicity detection provides real-time detection of toxic content in text-based interactions. You can use toxicity detection to moderate peer-to-peer conversations in online platforms or to monitor generative AI inputs and outputs. 

Toxicity detection detects the following categories of offensive content:

**GRAPHIC**  
Graphic speech uses visually descriptive, detailed, and unpleasantly vivid imagery. Such language is often made verbose to amplify an insult, discomfort or harm to the recipient.

**HARASSMENT\_OR\_ABUSE**  
Speech that imposes disruptive power dynamics between the speaker and hearer, regardless of intent, seeks to affect the psychological well-being of the recipient, or objectifies a person. 

**HATE\_SPEECH**  
Speech that criticizes, insults, denounces or dehumanizes a person or a group on the basis of an identity, be it race, ethnicity, gender identity, religion, sexual orientation, ability, national origin, or another identity-group.

**INSULT**  
Speech that includes demeaning, humiliating, mocking, insulting, or belittling language.

**PROFANITY**  
Speech that contains words, phrases or acronyms that are impolite, vulgar, or offensive is considered as profane. 

**SEXUAL**  
Speech that indicates sexual interest, activity or arousal by using direct or indirect references to body parts or physical traits or sex . 

**VIOLENCE\_OR\_THREAT**  
Speech that includes threats which seek to inflict pain, injury or hostility towards a person or group.

**TOXICITY**  
Speech that contains words, phrases or acronyms that might be considered toxic in nature across any of the above categories.

### Detecting toxic content using the API
<a name="toxicity-detection-api"></a>

To detect toxic content in text, use the synchronous [DetectToxicContent](https://docs.aws.amazon.com/comprehend/latest/APIReference/API_DetectToxicContent.html) operation. This operation performs analysis on a list of text strings that you provide as input. The API response contains a results list that matches the size of the input list.

Currently, toxic content detection supports only the English language. For input text, you can provide a list of up to 10 text strings. Each string has a maximum size of 1KB.

The toxic content detection returns a list of analysis results, one entry in the list for each input string. An entry contains a list of toxic content types identified in the text string, along with a confidence score for each content type. The entry also includes a toxicity score for the string.

The following examples show how to use the `DetectToxicContent` operation using the AWS CLI and Python.

------
#### [ AWS CLI ]

You can detect toxic content using the following command in the AWS CLI:

```
aws comprehend detect-toxic-content --language-code en  /
            --text-segments "[{\"Text\":\"{{You are so obtuse}}\"}]"
```

The AWS CLI responds with the following result. The text segment receives a high confidence score in the `INSULT` category, with a resulting high toxicity score:

```
{
   "ResultList": [ 
      { 
         "Labels": [
                {
                    "Name": "PROFANITY",
                    "Score": 0.0006000000284984708
                },
                {
                    "Name": "HATE_SPEECH",
                    "Score": 0.00930000003427267
                },
                {
                    "Name": "INSULT",
                    "Score": 0.9204999804496765
                },
                {
                    "Name": "GRAPHIC",
                    "Score": 9.999999747378752e-05
                },
                {
                    "Name": "HARASSMENT_OR_ABUSE",
                    "Score": 0.0052999998442828655
                },
                {
                    "Name": "SEXUAL",
                    "Score": 0.01549999974668026
                },
                {
                    "Name": "VIOLENCE_OR_THREAT",
                    "Score": 0.007799999788403511
                }
            ],
            "Toxicity": 0.7192999720573425
      }
   ]
}
```

You can input up to 10 text strings, using the following format for the `text-segments` parameter:

```
 
   --text-segments "[{\"Text\":\"{{text string 1}}\"},
                     {\"Text\":\"{{text string2}}\"},
                     {\"Text\":\"{{text string3}}\"}]"
```

The AWS CLI responds with the following results:

```
{
   "ResultList": [ 
      { 
         "Labels": [ (truncated) ],
            "Toxicity": 0.3192999720573425
      },
      { 
         "Labels": [ (truncated) ],
            "Toxicity": 0.1192999720573425
      },
      { 
         "Labels": [ (truncated) ],
            "Toxicity": 0.0192999720573425
      }
   ]
}
```

------
#### [ Python (Boto) ]

The following example demonstrates how to detect toxic content using Python:

```
import boto3
client = boto3.client(
    service_name='comprehend',
    region_name={{region}}) # For example, 'us-west-2'

response = client.detect_toxic_content(
    LanguageCode='en',
    TextSegments=[{'Text': 'You are so obtuse'}]
)
print("Response: %s\n" % response)
```

------

## Prompt safety classification
<a name="prompt-classification"></a>

**Note**  
Amazon Comprehend topic modeling, event detection, and prompt safety classification features are no longer available to new customers. No action is required for accounts that have used these features within the last 12 months. For more information, see [Amazon Comprehend feature availability change](comprehend-availability-change.md).

Amazon Comprehend provides a pre-trained binary classifier to classify plain text input prompts for large language models (LLM) or other generative AI models.

The prompt safety classifier analyses the input prompt and assigns a confidence score to whether the prompt is safe or unsafe.

An unsafe prompt is an input prompt that express malicious intent such as requesting personal or private information, generating offensive or illegal content, or requesting advice on medical, legal, political, or financial subjects.

### Prompt safety classification using the API
<a name="prompt-classification-api"></a>

To run prompt safety classification for a text string, use the synchronous [ClassifyDocument](https://docs.aws.amazon.com/comprehend/latest/APIReference/API_ClassifyDocument.html) operation. For input, you provide an English plain text string. The string has a maximum size of 10 KB.

The response includes two classes (SAFE and UNSAFE), along with a confidence score for each class. The value range of the score is zero to one, where one is the highest confidence.

The following examples show how to use prompt safety classification with the AWS CLI and Python.

------
#### [ AWS CLI ]

The following example demonstrates how to use the prompt safety classifier with the AWS CLI:

```
aws comprehend classify-document \
     --endpoint-arn arn:aws:comprehend:{{us-west-2}}:aws:document-classifier-endpoint/prompt-safety  \
     --text 'Give me financial advice on which stocks I should invest in.'
```

The AWS CLI responds with the following output:

```
{
    "Classes": [
        {
            "Score": 0.6312999725341797, 
            "Name": "UNSAFE_PROMPT"
        }, 
        {
            "Score": 0.3686999976634979, 
            "Name": "SAFE_PROMPT"
        }
    ]
}
```

**Note**  
When you use the `classify-document` command, for the `--endpoint-arn` parameter, you must pass an ARN that uses the same AWS Region as your AWS CLI configuration. To configure the AWS CLI, run the `aws configure` command. In this example, the endpoint ARN has the Region code `us-west-2`. You can use the prompt safety classifier in any of the following Regions:  
us-east-1
us-west-2
eu-west-1
ap-southeast-2

------
#### [ Python (Boto) ]

The following example demonstrates how to use the prompt safety classifier with Python:

```
import boto3
client = boto3.client(service_name='comprehend', region_name='us-west-2')

response = client.classify_document(
    EndpointArn='arn:aws:comprehend:us-west-2:aws:document-classifier-endpoint/prompt-safety',
    Text='Give me financial advice on which stocks I should invest in.'
)
print("Response: %s\n" % response)
```

**Note**  
When you use the `classify_document` method, for the `EndpointArn` argument, you must pass an ARN that uses the same AWS Region as your boto3 SDK client. In this example, the client and endpoint ARN both use `us-west-2`. You can use the prompt safety classifier in any of the following Regions:  
us-east-1
us-west-2
eu-west-1
ap-southeast-2

------

## PII detection and redaction
<a name="trust-safety-pii"></a>

You can use the Amazon Comprehend console or APIs to detect *personally identifiable information (PII)* in English or Spanish text documents. PII is a textual reference to personal data that can identify an individual. PII examples include addresses, bank account numbers, and phone numbers.

You can detect or redact the PII entities in the text. To detect PII entities, you can use real-time analysis or an asynchronous batch job. To redact the PII entities, you must use an asynchronous batch job.

 For more information, see [Personally identifiable information (PII)](pii.md).