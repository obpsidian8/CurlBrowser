The purpose of this library is to send curl requests within python. Essentially, I am mimicking the requests sent by browsers under the hood to servers they communicate with.

I developed this by examing the request sent by my browser to different sites via the network tab of the developer window, and copying the various requests sent using the "copy as curl option". Then I began examining the diffennt stages of browser requests and serve responses to obtain resources.

Of course this can be done using the built in python requests module but looking into the source code of python requests, there are some headers added by default and I wanted to be able to specify every bit of information sent in a request.

The file to run needs to be in the main directory. (The same directory containing the RunTestCases.py file.

See RunTestCases.py file for examples/ demos.
