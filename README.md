<div align="center">

<img src="docs/assets/logo.svg" alt="EnvelopeSeal wordmark: a closed envelope whose seal is a single filled square, next to the name EnvelopeSeal" width="240" />

# EnvelopeSeal

</div>

<table border="1">
<tr>
<td width="33%" valign="top">
<b>data key</b><br/>
A key that directly encrypts application data. Written <code>dek</code> in the
manifest. It is the thing you are ultimately protecting, and it is never meant
to sit unwrapped.
</td>
<td width="33%" valign="top">
<b>key encrypting key</b><br/>
A key whose only job is to wrap other keys. Written <code>kek</code> in the
manifest. A key encrypting key may wrap data keys or other key encrypting keys,
forming a hierarchy.
</td>
<td width="33%" valign="top">
<b>wrap</b><br/>
To encrypt one key under another. If A wraps B, then holding A lets you recover
B. An arrow in the graph points from the wrapping key down to the key it wraps.
</td>
</tr>
</table>

EnvelopeSeal is an offline auditor for an envelope encryption key hierarchy. You
give it a manifest that lists your keys and which key wraps which, and it checks
the hierarchy the way you would check a graph: are all the data keys actually
covered, is anything protected by something weaker than itself, are there loops,
is anything floating loose, and is anything past the date it should have been
rotated. It then reports blast radius, the number of data keys that fall if a
single key encrypting key is compromised.

It reads a manifest and prints text. It does not hold key material, it does not
talk to a key management service, and it opens no sockets. Everything it needs
is in the manifest you hand it and the as-of date you pass on the command line.

## Why this exists

Envelope encryption is easy to draw on a whiteboard and easy to get subtly wrong
in practice. A data key is wrapped by a key encrypting key, which may itself be
wrapped by another key encrypting key, up to some root. The diagram looks like a
tidy tree. The reality drifts. Someone adds a data key and forgets to wrap it.
Someone rotates a root and points a new key at an old one, closing a loop.
Someone provisions a 2048 bit RSA key to wrap a 256 bit symmetric key, quietly
capping the strength of everything below it. Someone leaves a key in the
manifest that nothing references any more.

None of these are visible from a single key's metadata. They are properties of
the graph. EnvelopeSeal loads the whole graph and asks the questions that only
make sense at the graph level, then prints the answers as plain lines you can
diff between runs.

The blast radius question is the one that changes behaviour. Every key
