import { BACKEND_URL } from "@/config"

export async function isSignedIn(): Promise<boolean> {
    try {
        const res = await fetch(BACKEND_URL + '/verify-token', {
            headers: {
                Authorization: `Bearer ${localStorage.getItem('access_token')}`,
            },
        });

        if (res.ok) return true;
        else return false;
    } catch(err) {
        console.error(err);
        return false;
    }
}