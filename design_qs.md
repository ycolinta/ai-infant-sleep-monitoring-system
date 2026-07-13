1\. A response schema was provided to both AI's as a template to format their responses. Snake case convention was used.



\----------------- Response Schema Given -----------------------------

RESPONSE\_SCHEMA = {

&#x20;   "type": "object",

&#x20;   "properties": {

&#x20;       "no\_apparent\_safety\_concerns": {

&#x20;           "type": "boolean"

&#x20;       },

&#x20;       "possible\_safety\_concerns": {

&#x20;           "type": "boolean"

&#x20;       },

&#x20;       "serious\_safety\_concerns": {

&#x20;           "type": "boolean"

&#x20;       },

&#x20;       "explanation": {

&#x20;           "type": "string"

&#x20;       }

&#x20;   },

&#x20;   "required": \[

&#x20;       "no\_apparent\_safety\_concerns",

&#x20;       "possible\_safety\_concerns",

&#x20;       "serious\_safety\_concerns",

&#x20;       "explanation"

&#x20;   ],

&#x20;   "additionalProperties": False

}



\----------------- Parent's response structure -----------------------



This is the way I, the parent, structured my responses:

{

&#x20; "file\_name": "image1.jpeg",

&#x20; "no\_apparent\_safety\_concerns": false,

&#x20; "possible\_safety\_concerns": true,

&#x20; "serious\_safety\_concerns": false,

&#x20; "explanation": "There is a soft blanket around the child's lower body that may pose a hazard..."

}



\----------------- Gemini model's response structure -----------------

{

&#x20;   "No apparent safety concerns.": false,

&#x20;   "Possible safety concerns.": false,

&#x20;   "Serious safety concerns.": true,

&#x20;   "explanation": "There are serious safety concerns in this sleep environment. A soft..."

}



\----------------- OpenAI model's response structure -----------------

{

&#x20;   "no\_apparent\_safety\_concerns": false,

&#x20;   "possible\_safety\_concerns": true,

&#x20;   "serious\_safety\_concerns": false,

&#x20;   "explanation": "The infant is sleeping on their side rather than on their back, which..."

}





Gemini's model did not adhere to the 'snake case' syntax given in the response schema, opting to use 'sentence case' in where the first letter of the first word in each of the three sentence labels was capitalized. The last label, 'explanation', was in lowercase.



\########################  Questions raised 



When comparing assessments accross models, will Gemini's format cause issues? 

Should I provide more instructions to Gemini to adhere to this structure? 

Do I instruct models to also include a field called file\_name to record the current image's name for ID? 



2\. This is the prompt that was given to the AI models:



"""

&#x20;       You are assisting with the assessment of child sleep environments for a computer science research project.

&#x20;       Analyze the child sleep environment shown in this image.

&#x20;       Based only on the visible information, determine whether the image shows:

&#x20;       

&#x20;       - No apparent safety concerns.

&#x20;       - Possible safety concerns.

&#x20;       - Serious safety concerns.

&#x20;       

&#x20;       Exactly one category must be true. The other two must be false.

&#x20;       

&#x20;       Briefly explain the observations that led to your assessment in the explanation field.



&#x20;       Return only one valid JSON object. Do not include Markdown code fences or any text outside the JSON object.       

"""



Both AI models adhered to the instruction given of analyzing child sleep environment shown in the images. However, when asked for the explanation, AI models did use the explanation field to write observations found in the images, but did not explain the distinction in assigning 'True' for one label over the other using those observations.



\########################  Questions raised 

Should the prompt be redefined to prompt the AI to explain why it assigned one label over the other in the explanation field?



The prompt included instructions to not include Markdown code fences or any text outside the JSON object. Gemini's output did return the JSON object inside a fenced block (```). A function was written to clean possible markdown code and save this output into the image's json files. 



\########################  Questions raised 

Should I rely on a function to clean possible markdown text found in AI responses or find a better way to emphasize to the AI models to not include anything outside the JSON object?



3\. Begin designing the relational schema or model of a database. 



Entities include different **intelligent models** such as Gemini, OpenAI, Parent. 

These intelligent models are analyzing **images**. 

When intelligent models analyze images they produce **responses**. 



Observations from entities so far:



(Intelligent models and images relationship)

One intelligent model has many images to analyze. 

An image can be analyzed by many intelligent models. 

**This is a many to many relationship.** 



(Intelligent models and responses relationship)

One intelligent model has many responses.

A response has only one intelligent model. 

**This is a one to many relationship.**



(Images and responses relationship)

**(Response** is another entity).

One image can have many responses. 

A response is tied to only one particular image. 

**This is a one to many relationship.** 



**One of the key questions when identifying attributes is:**



**Does this attribute describe the entity itself, or does it describe a relationship or an event involving that entity?**



Intelligent model(intelligent\_model\_id, intelligent\_model\_name)

Image(image\_id, file\_path, file\_ext) 

Response(response\_id, image\_id, model\_id, no\_apparent\_safety\_concerns, possible\_safety\_concerns, serious\_safety\_concerns, explanation)

Comparison









