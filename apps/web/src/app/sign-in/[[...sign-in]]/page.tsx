import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-black">
      <SignIn
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "bg-[#111] border border-white/10 shadow-2xl",
            headerTitle: "text-white",
            headerSubtitle: "text-white/60",
            formFieldInput: "bg-black border-white/20 text-white",
            formButtonPrimary:
              "bg-white text-black hover:bg-white/90 font-semibold",
            footerActionLink: "text-white/60 hover:text-white",
          },
        }}
      />
    </div>
  );
}
