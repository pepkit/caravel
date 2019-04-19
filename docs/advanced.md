# Advanced caravel features



## Security in `caravel`

`Caravel` uses an authentication token printed to your terminal to provide security. This way others are not able to connect to your `caravel` session and execute `looper` commands as _you_ on the remote server. 

By default the token is randomly generated upon `caravel` launch, but can be also set in the `.token_caravel` dotfile like:

```yaml
token: ABCD1234
```

Keep in mind that this is a less secure way of authentication as the token is exposed to ones that have the access to the `.token_caravel` file. Therefore make sure to set proper read permissions for this file.

## Verbosity of `caravel`

Both `looper` and `caravel` logging levels can be changed by toggling the debug mode at the server launch (`-d`, `--dbg` options). 
By default all the errors, warnings and information are displayed. The debug logs are activated when in debug mode.


## Debug/development mode

```bash
caravel -c example_caravel.yaml -d
```
This will trigger the unsecured mode (no URL token required); point the browser to: http://127.0.0.1:5000 (by default)
