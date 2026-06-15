from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken

class CustomJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        
        try:
            validated_token = self.get_validated_token(raw_token)
            
        except InvalidToken:
            raise AuthenticationFailed({
                "status":"failed",
                "message":"Token is expired."
            })
        
        user = self.get_user(validated_token)

        token_version = validated_token.get("token_version")
        
        if token_version != user.token_version:
            raise AuthenticationFailed({
                "status":"failed",
                "message":"Token has been invalidated please login again",
            }
            )

        return (user,validated_token)
    

