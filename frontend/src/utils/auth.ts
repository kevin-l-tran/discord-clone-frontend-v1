import { BACKEND_URL } from "@/config"

export async function isLoggedIn(): Promise<boolean> {
    try {
        const res = await fetch(BACKEND_URL + '/authorize', {
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